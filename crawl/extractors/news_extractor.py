"""News and announcement extractor."""
from typing import List, Optional
from bs4 import BeautifulSoup
import hashlib
from .base import BaseExtractor
from models import NewsArticle, Entity


class NewsExtractor(BaseExtractor):
    """Extract news articles and announcements."""
    
    def extract(self, html: str, markdown: str, url: str) -> List[Entity]:
        """Extract news articles from page."""
        soup = BeautifulSoup(html, "html.parser")
        entities = []
        
        # Strategy 1: Look for article tags
        articles = soup.find_all("article")
        if articles:
            for article in articles:
                entity = self._extract_from_article(article, url)
                if entity:
                    entities.append(entity)
        else:
            # Strategy 2: Extract from main content
            entity = self._extract_from_main_content(soup, markdown, url)
            if entity:
                entities.append(entity)
                
        return entities
        
    def _extract_from_article(self, article: BeautifulSoup, url: str) -> Optional[NewsArticle]:
        """Extract news article from article tag."""
        # Extract headline
        headline_elem = article.find(["h1", "h2", "h3"])
        if not headline_elem:
            return None
            
        headline = headline_elem.get_text(strip=True)
        
        # Extract publication date
        date_elem = article.find("time")
        publication_date = None
        if date_elem:
            publication_date = self.parse_date(date_elem.get("datetime") or date_elem.get_text())
            
        # Extract author
        author_elem = article.find(class_=lambda x: x and "author" in x.lower())
        author = author_elem.get_text(strip=True) if author_elem else None
        
        # Extract category
        category_elem = article.find(class_=lambda x: x and "category" in x.lower())
        category = category_elem.get_text(strip=True) if category_elem else None
        
        # Extract body
        body = article.get_text(separator=" ", strip=True)
        
        # Generate entity ID
        entity_id = hashlib.sha256(
            f"{url}_{headline}".encode()
        ).hexdigest()
        
        return NewsArticle(
            entity_id=entity_id,
            source_url=url,
            headline=self.clean_text(headline),
            publication_date=publication_date,
            author=self.clean_text(author),
            category=self.clean_text(category),
            body=self.clean_text(body),
            metadata={"extraction_method": "article_tag"}
        )
        
    def _extract_from_main_content(self, soup: BeautifulSoup, markdown: str, url: str) -> Optional[NewsArticle]:
        """Extract news from main content area."""
        # Find main heading
        headline_elem = soup.find("h1")
        if not headline_elem:
            return None
            
        headline = headline_elem.get_text(strip=True)
        
        # Use markdown for body
        body = markdown
        
        # Generate entity ID
        entity_id = hashlib.sha256(
            f"{url}_{headline}".encode()
        ).hexdigest()
        
        return NewsArticle(
            entity_id=entity_id,
            source_url=url,
            headline=self.clean_text(headline),
            body=self.clean_text(body),
            metadata={"extraction_method": "main_content"}
        )
