# IndiaAI Impact Crawler

A production-ready web scraper built with Crawl4AI that extracts structured, RAG-ready content from the IndiaAI Impact Summit website.

## Features

- **Async crawling** with Crawl4AI and Playwright
- **Structured entity extraction** for agenda items, events, exhibitions, initiatives, and news
- **Semantic chunking** with heading awareness for RAG pipelines
- **URL frontier** with priority queue and crash recovery
- **Anti-bot resilience** with progressive escalation
- **Comprehensive logging** and metrics tracking

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

## Quick Start

```bash
# Run crawler with default settings
python main.py

# Crawl with custom settings
python main.py --max-pages 100 --output-dir ./my_output

# Start fresh (clear frontier database)
python main.py --fresh

# Custom seed URLs
python main.py --seeds https://impact.indiaai.gov.in/agenda https://impact.indiaai.gov.in/working-groups
```

## Configuration

Edit `.env` file (copy from `.env.example`):

```bash
MAX_CONCURRENT_REQUESTS=5
MAX_DEPTH=3
MAX_PAGES_PER_RUN=500
REQUEST_DELAY_SECONDS=2
CHUNK_SIZE_TOKENS=800
```

## Output Structure

```
output/
├── documents/          # PageDocument JSON files (one per URL)
├── chunks/             # RAG-ready chunk JSON files
├── pdfs/               # Downloaded PDFs
└── logs/               # Crawl logs and metrics
```

## Entity Types

- **Agenda Items**: Day-wise schedule entries with times and descriptions
- **Events**: Working-group events with dates, locations, and registration links
- **Exhibitions**: Expo information from PDFs and pages
- **Initiatives**: Challenge guides and calls
- **News**: Announcements and press releases

## RAG Integration

Each chunk includes:
- `chunk_id`: Unique identifier
- `text`: Chunk content
- `metadata`: Filters for retrieval (content_type, dates, working_group, etc.)
- `source_url`: Citation link
- `anchor_heading`: Context heading

Load chunks into your vector DB:

```python
import json
from pathlib import Path

chunks_dir = Path("output/chunks")
for chunk_file in chunks_dir.glob("*.json"):
    with open(chunk_file) as f:
        chunk = json.load(f)
        # Insert into vector DB
        # vector_db.insert(chunk["chunk_id"], chunk["text"], chunk["metadata"])
```

## Architecture

- `main.py`: CLI entry point
- `crawler.py`: Main orchestrator
- `frontier.py`: URL queue management
- `extractors/`: Content-type specific extractors
- `chunker.py`: Semantic chunking
- `config.py`: Configuration management
- `models.py`: Pydantic data models

## License

MIT
