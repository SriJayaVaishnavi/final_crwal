"""Crawl a single URL and export immediately."""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from frontier import URLFrontier
from crawler import IndiaAICrawler
from logger import setup_logger
from config import config
from export_data import export_all_data


logger = setup_logger("single_url_crawler")


def crawl_single_url(url: str, section_name: str):
    """Crawl a single URL and export immediately."""
    print(f"\n{'='*60}")
    print(f"CRAWLING: {url}")
    print(f"{'='*60}\n")
    
    # Setup output directory
    section_output_dir = Path("output") / section_name
    section_output_dir.mkdir(parents=True, exist_ok=True)
    (section_output_dir / "documents").mkdir(exist_ok=True)
    (section_output_dir / "chunks").mkdir(exist_ok=True)
    (section_output_dir / "pdfs").mkdir(exist_ok=True)
    (section_output_dir / "logs").mkdir(exist_ok=True)
    
    config.output_dir = section_output_dir
    
    # Initialize frontier
    frontier_db = Path(f"frontier_{section_name}_single.db")
    if frontier_db.exists():
        frontier_db.unlink()
    
    frontier = URLFrontier(frontier_db)
    frontier.enqueue(url, depth=0)
    
    # Create crawler
    crawler = IndiaAICrawler(frontier)
    
    # Crawl just this one URL
    asyncio.run(crawler.crawl(max_pages=1))
    
    # Export immediately
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    url_slug = url.split('/')[-1] or 'homepage'
    export_filename = f"{section_name}_{url_slug}_{timestamp}.json"
    export_path = export_all_data(section_output_dir, export_filename)
    
    print(f"\n{'='*60}")
    print(f"✓ Exported to: {export_path.name}")
    print(f"{'='*60}\n")
    
    return export_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python crawl_single_url.py <url> <section_name>")
        sys.exit(1)
    
    url = sys.argv[1]
    section_name = sys.argv[2]
    crawl_single_url(url, section_name)
