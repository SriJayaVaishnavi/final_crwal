"""Simple single URL crawler - no chunking, just save the page."""
import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from frontier import URLFrontier
from crawler import IndiaAICrawler
from config import config
import json


def crawl_url_simple(url: str, section_name: str):
    """Crawl one URL and save immediately - no chunking."""
    print(f"\nCrawling: {url}")
    
    # Setup output
    output_dir = Path("output") / section_name
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "documents").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    config.output_dir = output_dir
    
    # Crawl
    frontier_db = Path(f"frontier_temp.db")
    if frontier_db.exists():
        frontier_db.unlink()
    
    frontier = URLFrontier(frontier_db)
    frontier.enqueue(url, depth=0)
    crawler = IndiaAICrawler(frontier)
    
    asyncio.run(crawler.crawl(max_pages=1))
    
    # Export all documents
    docs = []
    for doc_file in (output_dir / "documents").glob("*.json"):
        with open(doc_file, 'r', encoding='utf-8') as f:
            docs.append(json.load(f))
    
    # Save
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    url_slug = url.split('/')[-1] or 'page'
    # Sanitize slug for Windows filenames
    url_slug = url_slug.replace('?', '_').replace('&', '_').replace('=', '_')
    filename = f"{section_name}_{url_slug}_{timestamp}.json"
    output_file = output_dir / filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"documents": docs, "url": url, "timestamp": timestamp}, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved: {filename}\n")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python simple_crawl.py <url> <section>")
        sys.exit(1)
    crawl_url_simple(sys.argv[1], sys.argv[2])
