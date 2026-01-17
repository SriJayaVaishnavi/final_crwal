"""Crawl a specific section of the IndiaAI Impact website."""
import sys
import os
import asyncio
import argparse
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
from logger import setup_logger, metrics
from config import config
from sections import get_section, get_all_sections
from export_data import export_all_data


logger = setup_logger("section_crawler")


def main():
    """Main entry point for section-based crawling."""
    parser = argparse.ArgumentParser(description="IndiaAI Section Crawler")
    parser.add_argument(
        "section",
        help="Section ID to crawl (e.g., 'agenda', 'working_groups')"
    )
    parser.add_argument(
        "--list-sections",
        action="store_true",
        help="List all available sections"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output"),
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    # List sections if requested
    if args.list_sections:
        print("\n" + "="*60)
        print("AVAILABLE SECTIONS")
        print("="*60)
        for section_id, section_info in get_all_sections():
            print(f"\n{section_info['priority']}. {section_id}")
            print(f"   Name: {section_info['name']}")
            print(f"   Description: {section_info['description']}")
            print(f"   Seeds: {len(section_info['seeds'])} URLs")
            print(f"   Max Pages: {section_info['max_pages']}")
        print("="*60)
        return
    
    # Get section configuration
    section = get_section(args.section)
    if not section:
        print(f"Error: Unknown section '{args.section}'")
        print("Use --list-sections to see available sections")
        return
    
    print("\n" + "="*60)
    print(f"CRAWLING SECTION: {section['name']}")
    print("="*60)
    print(f"Description: {section['description']}")
    print(f"Seeds: {len(section['seeds'])} URLs")
    print(f"Max Pages: {section['max_pages']}")
    print("="*60 + "\n")
    
    # Setup output directory for this section
    section_output_dir = args.output_dir / args.section
    section_output_dir.mkdir(parents=True, exist_ok=True)
    (section_output_dir / "documents").mkdir(exist_ok=True)
    (section_output_dir / "chunks").mkdir(exist_ok=True)
    (section_output_dir / "pdfs").mkdir(exist_ok=True)
    (section_output_dir / "logs").mkdir(exist_ok=True)
    
    # Update config
    config.output_dir = section_output_dir
    
    # Initialize frontier with section-specific database
    frontier_db = Path(f"frontier_{args.section}.db")
    if frontier_db.exists():
        frontier_db.unlink()
        logger.info(f"Cleared section frontier database: {frontier_db}")
    
    frontier = URLFrontier(frontier_db)
    
    # Enqueue section seeds
    for seed in section['seeds']:
        frontier.enqueue(seed, depth=0)
        logger.info(f"Enqueued: {seed}")
    
    # Show frontier stats
    stats = frontier.get_stats()
    logger.info(f"Frontier stats: {stats}")
    
    # Create section filter function
    from sections import url_matches_section
    section_filter = lambda url: url_matches_section(url, args.section)
    
    # Create crawler with section filter
    crawler = IndiaAICrawler(frontier, section_filter=section_filter)
    
    # Run crawl
    logger.info(f"Starting section crawl with max_pages={section['max_pages']}")
    asyncio.run(crawler.crawl(max_pages=section['max_pages']))
    
    # Show final stats
    final_stats = frontier.get_stats()
    logger.info(f"Final frontier stats: {final_stats}")
    
    metrics_summary = metrics.get_summary()
    logger.info(f"Crawl metrics: {metrics_summary}")
    
    # Export section data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_filename = f"{args.section}_data_{timestamp}.json"
    export_path = export_all_data(section_output_dir, export_filename)
    
    print("\n" + "="*60)
    print(f"SECTION CRAWL COMPLETE: {section['name']}")
    print("="*60)
    print(f"Pages attempted: {metrics_summary['pages_attempted']}")
    print(f"Pages succeeded: {metrics_summary['pages_succeeded']}")
    print(f"Pages failed: {metrics_summary['pages_failed']}")
    print(f"Entities extracted: {metrics_summary['entities_extracted']}")
    print(f"Chunks created: {metrics_summary['chunks_created']}")
    print(f"PDFs processed: {metrics_summary['pdfs_processed']}")
    print(f"\nSection output: {section_output_dir.absolute()}")
    print(f"Consolidated JSON: {export_path.absolute()}")
    print("="*60)
    print(f"\n✓ Section '{args.section}' complete!")
    print(f"✓ Save this file locally: {export_path.name}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
