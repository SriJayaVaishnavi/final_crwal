"""
Standalone script to scrape Key Participants from IndiaAI Impact homepage.
Extracts participant details and downloads their images.
"""
import sys
import os

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
import json
import aiohttp
from pathlib import Path
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib


async def scrape_key_participants():
    """Scrape all key participants from the homepage."""
    url = "https://impact.indiaai.gov.in/"
    
    # Create output directories
    output_dir = Path("output/key_participants")
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)
    
    print(f"Starting scrape of Key Participants from {url}")
    print(f"Output directory: {output_dir.absolute()}")
    
    # Configure browser
    browser_config = BrowserConfig(
        headless=False,
        verbose=True,
        viewport_width=1920,
        viewport_height=1080,
    )
    
    # Configure crawler with JS to click "View All"
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,  # 120 seconds
        wait_until="domcontentloaded",  # Less strict than networkidle
        js_code=[
            # Wait for page to load and click "View All"
            """
            await new Promise(r => setTimeout(r, 3000));
            const viewAllBtn = Array.from(document.querySelectorAll('button')).find(el => 
                el.textContent.includes('View All')
            );
            if (viewAllBtn) {
                viewAllBtn.click();
                await new Promise(r => setTimeout(r, 3000));
            }
            """,
        ],
        delay_before_return_html=2.0,
    )
    
    participants = []
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("Crawling page...")
        result = await crawler.arun(url=url, config=crawler_config)
        
        if not result.success:
            print(f"Error: {result.error_message}")
            return
        
        print("Parsing HTML...")
        soup = BeautifulSoup(result.html, "html.parser")
        
        # Find all participant cards using the grid container
        # After "View All" is clicked, participants are in a grid
        participant_cards = soup.select("div.tw\\:grid div")
        
        # Filter to actual participant cards (those with images and names)
        actual_cards = []
        for card in participant_cards:
            name_elem = card.select_one("span.tw\\:typography-headline-4")
            img_elem = card.select_one("img.tw\\:object-cover")
            if name_elem and img_elem:
                actual_cards.append(card)
        
        print(f"Found {len(actual_cards)} participant cards")
        
        # Extract data from each card
        for idx, card in enumerate(actual_cards, 1):
            try:
                # Extract name
                name_elem = card.select_one("span.tw\\:typography-headline-4")
                name = name_elem.get_text(strip=True) if name_elem else "Unknown"
                
                # Extract title and organization (combined in one element)
                title_org_elem = card.select_one("div.tw\\:text-grey-400.tw\\:text-sm")
                title_org = title_org_elem.get_text(strip=True) if title_org_elem else ""
                
                # Try to split title and organization
                # Format is usually: "Title, Organization"
                if ", " in title_org:
                    parts = title_org.rsplit(", ", 1)
                    title = parts[0].strip()
                    organization = parts[1].strip() if len(parts) > 1 else ""
                else:
                    title = title_org
                    organization = ""
                
                # Extract image URL
                img_elem = card.select_one("img.tw\\:object-cover")
                img_url = img_elem.get("src") if img_elem else None
                
                # Make image URL absolute
                if img_url:
                    img_url = urljoin(url, img_url)
                
                participant = {
                    "id": idx,
                    "name": name,
                    "title": title,
                    "organization": organization,
                    "image_url": img_url,
                    "image_filename": None,
                }
                
                # Download image
                if img_url:
                    try:
                        image_filename = await download_image(img_url, images_dir, name)
                        participant["image_filename"] = image_filename
                        print(f"  [{idx}/{len(actual_cards)}] {name} - Image downloaded")
                    except Exception as e:
                        print(f"  [{idx}/{len(actual_cards)}] {name} - Image download failed: {e}")
                else:
                    print(f"  [{idx}/{len(actual_cards)}] {name} - No image URL")
                
                participants.append(participant)
                
            except Exception as e:
                print(f"Error extracting participant {idx}: {e}")
                continue
    
    # Save JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_dir / f"key_participants_{timestamp}.json"
    
    output_data = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "source_url": url,
        "total_participants": len(participants),
        "participants": participants,
    }
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Scraping complete!")
    print(f"✓ Total participants: {len(participants)}")
    print(f"✓ JSON saved to: {json_file.name}")
    print(f"✓ Images saved to: {images_dir.absolute()}")
    print(f"{'='*60}\n")
    
    return json_file


async def download_image(url: str, images_dir: Path, participant_name: str) -> str:
    """Download an image and save it locally."""
    # Create a safe filename from participant name
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in participant_name)
    safe_name = safe_name.replace(' ', '_').lower()
    
    # Get file extension from URL
    ext = Path(url).suffix
    if not ext or ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        ext = '.jpg'
    
    filename = f"{safe_name}{ext}"
    filepath = images_dir / filename
    
    # Download image
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                content = await response.read()
                with open(filepath, "wb") as f:
                    f.write(content)
                return filename
            else:
                raise Exception(f"HTTP {response.status}")


if __name__ == "__main__":
    asyncio.run(scrape_key_participants())
