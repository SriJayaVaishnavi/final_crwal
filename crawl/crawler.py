"""Main crawler orchestrator."""
import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import aiohttp
import os

from config import config
from models import PageDocument, ContentType, OutboundLink, CrawlResult
from frontier import URLFrontier
from url_utils import (
    canonicalize_url,
    is_in_scope,
    is_pdf,
    classify_url,
    extract_links,
    classify_link_text,
    extract_section_path
)
from extractors import AgendaExtractor, EventExtractor, NewsExtractor
from chunker import SemanticChunker
from logger import setup_logger, metrics


logger = setup_logger("crawler")


class IndiaAICrawler:
    """Main crawler orchestrator for IndiaAI Impact website."""
    
    def __init__(self, frontier: URLFrontier, section_filter=None):
        self.frontier = frontier
        self.chunker = SemanticChunker()
        self.section_filter = section_filter  # Function to filter URLs by section
        
        # Initialize extractors
        self.extractors = {
            ContentType.AGENDA_ITEM: AgendaExtractor(),
            ContentType.EVENT: EventExtractor(),
            ContentType.WORKING_GROUP_PAGE: EventExtractor(),  # Events are in working-group pages
            ContentType.NEWS: NewsExtractor(),
        }
        
    async def crawl(self, max_pages: Optional[int] = None):
        """
        Main crawl loop.
        
        Args:
            max_pages: Maximum pages to crawl (None for unlimited)
        """
        logger.info("Starting crawl...")
        
        # Reset any in-progress URLs from previous crash
        self.frontier.reset_in_progress()
        
        # Configure browser with stealth mode (non-headless for better bypass)
        browser_config = BrowserConfig(
            headless=False,  # Visible browser bypasses detection better
            verbose=True,
            user_agent=config.user_agent,
            viewport_width=1920,
            viewport_height=1080,
            accept_downloads=False,
            extra_args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
            ]
        )
        
        # Configure crawler with JS execution
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=config.page_timeout_ms,
            wait_until="networkidle",
            js_code=[
                "window.scrollTo(0, document.body.scrollHeight / 2);",
                "await new Promise(r => setTimeout(r, 1000));",
            ],
            delay_before_return_html=2.0,  # Wait 2 seconds before extracting
        )
        
        pages_crawled = 0
        max_to_crawl = max_pages or config.max_pages_per_run
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            while pages_crawled < max_to_crawl:
                # Get next URL
                url_data = self.frontier.dequeue()
                if not url_data:
                    logger.info("No more URLs in frontier")
                    break
                    
                url, depth, url_hash = url_data
                
                # Check depth limit
                if depth > config.max_depth:
                    logger.info(f"Skipping {url} - depth {depth} exceeds limit")
                    self.frontier.mark_success(url_hash)
                    continue
                    
                logger.info(f"Crawling [{pages_crawled + 1}/{max_to_crawl}]: {url} (depth={depth})")
                
                try:
                    # Crawl page
                    result = await self._crawl_page(crawler, crawler_config, url, depth, url_hash)
                    
                    # Save result
                    if result.page_document:
                        self._save_result(result)
                        
                    pages_crawled += 1
                    metrics.increment("pages_succeeded")
                    
                    # Rate limiting
                    await asyncio.sleep(config.request_delay_seconds)
                    
                except Exception as e:
                    logger.error(f"Error crawling {url}: {e}", exc_info=True)
                    self.frontier.mark_failure(url_hash, str(e))
                    metrics.increment("pages_failed")
                    metrics.add_error(url, str(e))
                    
        logger.info(f"Crawl complete. Pages crawled: {pages_crawled}")
        metrics.save()
        
        # Auto-export consolidated JSON
        self._export_consolidated_json()
        
    async def _crawl_page(
        self,
        crawler: AsyncWebCrawler,
        crawler_config: CrawlerRunConfig,
        url: str,
        depth: int,
        url_hash: str
    ) -> CrawlResult:
        """Crawl a single page."""
        metrics.increment("pages_attempted")
        
        # Handle PDFs separately
        if is_pdf(url):
            return await self._crawl_pdf(url, url_hash)
            
        # Crawl HTML page
        result = await crawler.arun(url=url, config=crawler_config)
        
        if not result.success:
            raise Exception(f"Crawl failed: {result.error_message}")
            
        # Extract content
        html = result.html
        
        # Use new markdown API
        if hasattr(result.markdown, 'fit_markdown'):
            markdown = result.markdown.fit_markdown
        elif hasattr(result.markdown, 'raw_markdown'):
            markdown = result.markdown.raw_markdown
        else:
            markdown = str(result.markdown)
            
        # Fallback text extraction if markdown is empty
        if not markdown.strip():
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            markdown = soup.get_text(separator="\n\n", strip=True)
            logger.info(f"Used fallback text extraction for {url}")
        
        # Classify content type
        content_type = classify_url(url)
        
        # Extract entities
        entities = []
        if content_type in self.extractors:
            extractor = self.extractors[content_type]
            entities = extractor.extract(html, markdown, url)
            metrics.increment("entities_extracted", len(entities))
            
        # Extract outbound links
        outbound_links = self._extract_outbound_links(html, url)
        
        # Discover and enqueue new URLs
        discovered = self._discover_links(html, url, depth)
        logger.info(f"Discovered {discovered} new URLs from {url}")
        
        # Create page document
        doc_id = hashlib.sha256(canonicalize_url(url).encode()).hexdigest()
        
        page_doc = PageDocument(
            doc_id=doc_id,
            source_url=url,
            canonical_url=canonicalize_url(url),
            content_type=content_type,
            title=self._extract_title(html),
            section_path=extract_section_path(url),
            crawl_timestamp_utc=datetime.utcnow().isoformat() + "Z",
            raw_text=markdown,
            entities=entities,
            outbound_links=outbound_links,
            metadata={
                "depth": depth,
                "status_code": result.status_code,
            }
        )
        
        # Create chunks - DISABLED to prevent hanging on Windows
        # chunks = self.chunker.chunk(
        #     text=markdown,
        #     doc_id=doc_id,
        #     source_url=url,
        #     content_type=content_type.value,
        #     section_path=extract_section_path(url),
        #     metadata={}
        # )
        chunks = []  # Skip chunking to avoid hanging
        metrics.increment("chunks_created", len(chunks))
        
        # Mark as success
        self.frontier.mark_success(url_hash)
        
        return CrawlResult(
            url=url,
            status_code=result.status_code,
            success=True,
            crawl_timestamp=datetime.utcnow().isoformat() + "Z",
            page_document=page_doc,
            chunks=chunks
        )
        
    async def _crawl_pdf(self, url: str, url_hash: str) -> CrawlResult:
        """Handle PDF crawling and downloading."""
        logger.info(f"PDF detected: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Generate filename from URL
                        filename = url.split("/")[-1]
                        if not filename.endswith(".pdf"):
                            filename += ".pdf"
                            
                        # Save PDF
                        pdf_path = config.output_dir / "pdfs" / filename
                        with open(pdf_path, "wb") as f:
                            f.write(content)
                            
                        # Save metadata
                        meta = {
                            "url": url,
                            "filename": filename,
                            "size_bytes": len(content),
                            "downloaded_at": datetime.utcnow().isoformat() + "Z"
                        }
                        
                        meta_path = config.output_dir / "pdfs" / f"{filename}.json"
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump(meta, f, indent=2)
                            
                        metrics.increment("pdfs_processed")
                        logger.info(f"Downloaded PDF: {filename}")
                        
                        self.frontier.mark_success(url_hash)
                        return CrawlResult(
                            url=url,
                            success=True,
                            crawl_timestamp=datetime.utcnow().isoformat() + "Z",
                        )
        except Exception as e:
            logger.error(f"Error downloading PDF {url}: {e}")
            self.frontier.mark_failure(url_hash, str(e))
            return CrawlResult(url=url, success=False, error_message=str(e))
            
        self.frontier.mark_success(url_hash)
        return CrawlResult(
            url=url,
            success=True,
            crawl_timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
    def _extract_title(self, html: str) -> Optional[str]:
        """Extract page title."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Try h1 first
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
            
        # Fallback to title tag
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
            
        return None
        
    def _extract_outbound_links(self, html: str, base_url: str) -> List[OutboundLink]:
        """Extract outbound links with classification."""
        links = extract_links(html, base_url)
        
        outbound_links = []
        for href, text in links:
            link_type = classify_link_text(text)
            outbound_links.append(OutboundLink(
                href=href,
                text=text,
                link_type=link_type
            ))
            
        return outbound_links
        
    def _discover_links(self, html: str, base_url: str, current_depth: int) -> int:
        """Discover and enqueue new links."""
        links = extract_links(html, base_url)
        
        discovered = 0
        for href, _ in links:
            if is_in_scope(href):
                canonical = canonicalize_url(href)
                
                # Apply section filter if set
                if self.section_filter and not self.section_filter(canonical):
                    logger.debug(f"Skipping URL (not in section): {canonical}")
                    continue
                
                if self.frontier.enqueue(canonical, current_depth + 1, base_url):
                    discovered += 1
                    
        return discovered
        
    def _save_result(self, result: CrawlResult):
        """Save crawl result to disk."""
        if not result.page_document:
            return
            
        # Save page document
        doc_file = config.output_dir / "documents" / f"{result.page_document.doc_id}.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(result.page_document.model_dump(), f, indent=2, ensure_ascii=False)
            
        # Append to consolidated JSONL file
        jsonl_file = config.output_dir / "all_data.jsonl"
        with open(jsonl_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result.page_document.model_dump(), ensure_ascii=False) + "\n")
            
        # Save chunks
        for chunk in result.chunks:
            chunk_file = config.output_dir / "chunks" / f"{chunk.chunk_id}.json"
            with open(chunk_file, "w", encoding="utf-8") as f:
                json.dump(chunk.model_dump(), f, indent=2, ensure_ascii=False)
                
        logger.debug(f"Saved document {result.page_document.doc_id} with {len(result.chunks)} chunks")
        
    def _export_consolidated_json(self):
        """Export all scraped data to a consolidated JSON file."""
        try:
            from export_data import export_all_data
            export_path = export_all_data(config.output_dir)
            logger.info(f"Consolidated JSON exported to: {export_path}")
        except Exception as e:
            logger.error(f"Failed to export consolidated JSON: {e}")
