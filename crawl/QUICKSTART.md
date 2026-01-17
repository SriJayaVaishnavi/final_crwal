# Quick Start: Using Browser Subagent for Data Extraction

Since the IndiaAI Impact website has strong anti-bot protection (403 errors), here's how to extract data using the browser subagent tool:

## Method 1: Browser Subagent (Recommended)

```python
# Example: Extract agenda data
from browser_subagent import browser_subagent

# Navigate and extract
result = browser_subagent(
    TaskName="Extract Agenda Data",
    Task="""
    1. Navigate to https://impact.indiaai.gov.in/agenda
    2. Wait for page to fully load
    3. Extract all day sections and schedule items
    4. Return structured JSON with: day_name, time, title, description
    """,
    RecordingName="agenda_extraction"
)
```

## Method 2: Install Undetected ChromeDriver

Add to `requirements.txt`:
```
undetected-chromedriver>=3.5.0
```

Update `crawler.py` to use undetected mode:
```python
import undetected_chromedriver as uc

# In browser config
browser_config = BrowserConfig(
    use_managed_browser=False,  # Use external browser
    # ... other settings
)
```

## Method 3: Direct API Calls

Inspect browser network tab to find API endpoints, then make direct requests:
```python
import requests

# Example (if API exists)
response = requests.get(
    "https://impact.indiaai.gov.in/api/agenda",
    headers={"User-Agent": "Mozilla/5.0..."}
)
```

## Current Crawler Usage

The crawler is ready to use on other websites:

```bash
# Crawl a different site
python main.py --seeds https://example.com --max-pages 100

# With custom output
python main.py --seeds https://example.com --output-dir ./my_data
```
