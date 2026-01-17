"""CLI entry point for IndiaAI crawler."""
import asyncio
import argparse
from pathlib import Path
from frontier import URLFrontier
from crawler import IndiaAICrawler
from logger import setup_logger, metrics
from config import config


logger = setup_logger("main")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="IndiaAI Impact Crawler")
    parser.add_argument(
        "--seeds",
        nargs="+",
        default=["https://impact.indiaai.gov.in"],
        help="Seed URLs to start crawling"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=config.max_pages_per_run,
        help="Maximum pages to crawl"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.output_dir,
        help="Output directory"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh (clear frontier database)"
    )
    
    args = parser.parse_args()
    
    # Update config
    config.output_dir = args.output_dir
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize frontier
    frontier_db = Path("frontier.db")
    if args.fresh and frontier_db.exists():
        frontier_db.unlink()
        logger.info("Cleared frontier database")
        
    frontier = URLFrontier(frontier_db)
    
    # Enqueue seed URLs
    for seed in args.seeds:
        frontier.enqueue(seed, depth=0)
        logger.info(f"Enqueued seed: {seed}")
        
    # Add comprehensive high-value URLs from checklist
    from seeds import get_all_seeds
    comprehensive_seeds = get_all_seeds()
    
    for seed in comprehensive_seeds:
        if frontier.enqueue(seed, depth=0):
            logger.info(f"Enqueued comprehensive seed: {seed}")
        
    # Show frontier stats
    stats = frontier.get_stats()
    logger.info(f"Frontier stats: {stats}")
    
    # Create crawler
    crawler = IndiaAICrawler(frontier)
    
    # Run crawl
    logger.info(f"Starting crawl with max_pages={args.max_pages}")
    asyncio.run(crawler.crawl(max_pages=args.max_pages))
    
    # Show final stats
    final_stats = frontier.get_stats()
    logger.info(f"Final frontier stats: {final_stats}")
    
    metrics_summary = metrics.get_summary()
    logger.info(f"Crawl metrics: {metrics_summary}")
    
    print("\n" + "="*60)
    print("CRAWL COMPLETE")
    print("="*60)
    print(f"Pages attempted: {metrics_summary['pages_attempted']}")
    print(f"Pages succeeded: {metrics_summary['pages_succeeded']}")
    print(f"Pages failed: {metrics_summary['pages_failed']}")
    print(f"Entities extracted: {metrics_summary['entities_extracted']}")
    print(f"Chunks created: {metrics_summary['chunks_created']}")
    print(f"PDFs processed: {metrics_summary['pdfs_processed']}")
    print(f"\nOutput directory: {config.output_dir.absolute()}")
    print(f"Documents: {config.output_dir / 'documents'}")
    print(f"Chunks: {config.output_dir / 'chunks'}")
    print(f"Logs: {config.output_dir / 'logs'}")
    print("="*60)


if __name__ == "__main__":
    main()
