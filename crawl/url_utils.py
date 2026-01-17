"""URL utilities for normalization, classification, and link extraction."""
from urllib.parse import urlparse, urljoin, parse_qs, urlunparse
from typing import List, Tuple, Optional
import re
from bs4 import BeautifulSoup
from models import ContentType
from config import config


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL by:
    - Converting to lowercase domain
    - Removing UTM and tracking parameters
    - Normalizing trailing slash
    - Removing fragment
    """
    parsed = urlparse(url)
    
    # Lowercase domain
    netloc = parsed.netloc.lower()
    
    # Remove tracking parameters
    query_params = parse_qs(parsed.query)
    tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}
    clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}
    
    # Rebuild query string
    query_string = "&".join(f"{k}={v[0]}" for k, v in clean_params.items())
    
    # Normalize path (remove trailing slash unless it's root)
    path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    
    # Rebuild URL without fragment
    canonical = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        query_string,
        ""  # No fragment
    ))
    
    return canonical


def is_in_scope(url: str) -> bool:
    """Check if URL is within allowed domain."""
    parsed = urlparse(url)
    return parsed.netloc.lower() == config.allowed_domain.lower()


def is_pdf(url: str) -> bool:
    """Check if URL points to a PDF."""
    return url.lower().endswith(".pdf")


def classify_url(url: str) -> ContentType:
    """
    Classify URL based on path patterns.
    
    Priority:
    1. agenda -> AGENDA_ITEM
    2. working-groups -> WORKING_GROUP_PAGE
    3. events/*.pdf -> EXHIBITION or INITIATIVE_DOC
    4. media -> NEWS
    5. Default -> GENERIC_PAGE
    """
    path = urlparse(url).path.lower()
    
    if "agenda" in path:
        return ContentType.AGENDA_ITEM
    elif "working-group" in path:
        return ContentType.WORKING_GROUP_PAGE
    elif "event" in path:
        if is_pdf(url):
            # Will be further classified during extraction
            return ContentType.EXHIBITION
        return ContentType.EVENT
    elif "media" in path or "news" in path or "announcement" in path:
        return ContentType.NEWS
    else:
        return ContentType.GENERIC_PAGE


def get_url_priority(url: str) -> int:
    """
    Calculate URL priority for crawl queue.
    
    Priority scores:
    - agenda: 10
    - working-groups: 9
    - events: 8
    - PDFs: 7
    - media: 6
    - other: 5
    """
    path = urlparse(url).path.lower()
    
    if "agenda" in path:
        return 10
    elif "working-group" in path:
        return 9
    elif "event" in path:
        return 8
    elif is_pdf(url):
        return 7
    elif "media" in path or "news" in path:
        return 6
    else:
        return 5


def extract_links(html: str, base_url: str) -> List[Tuple[str, str]]:
    """
    Extract all links from HTML.
    
    Returns:
        List of (absolute_url, link_text) tuples
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        text = anchor.get_text(strip=True)
        
        # Convert to absolute URL
        absolute_url = urljoin(base_url, href)
        
        # Only include in-scope links
        if is_in_scope(absolute_url):
            links.append((absolute_url, text))
    
    return links


def classify_link_text(text: str) -> str:
    """
    Classify link based on text content.
    
    Returns: registration, eoi, download, or navigation
    """
    text_lower = text.lower()
    
    if any(keyword in text_lower for keyword in ["register", "registration", "sign up", "rsvp"]):
        return "registration"
    elif any(keyword in text_lower for keyword in ["eoi", "expression of interest", "apply"]):
        return "eoi"
    elif any(keyword in text_lower for keyword in ["download", "pdf", "brochure", "guide"]):
        return "download"
    else:
        return "navigation"


def extract_section_path(url: str) -> List[str]:
    """
    Extract section path from URL.
    
    Example: /working-groups/safe-trusted-ai -> ["Working Groups", "Safe & Trusted AI"]
    """
    path = urlparse(url).path.strip("/")
    if not path:
        return []
    
    segments = path.split("/")
    
    # Clean and title-case segments
    section_path = []
    for segment in segments:
        # Replace hyphens with spaces and title case
        cleaned = segment.replace("-", " ").title()
        section_path.append(cleaned)
    
    return section_path
