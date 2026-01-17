"""Section-based crawl configuration for IndiaAI Impact website."""

# Define all website sections/badges
SECTIONS = {
    "agenda": {
        "name": "Agenda",
        "description": "Main summit agenda and schedule",
        "seeds": [
            "https://impact.indiaai.gov.in/agenda",
        ],
        "max_pages": 20,
        "priority": 1,
    },
    
    "working_groups": {
        "name": "Working Groups (Chakras)",
        "description": "All 7 working group pages",
        "seeds": [
            "https://impact.indiaai.gov.in/working-groups",
            "https://impact.indiaai.gov.in/working-groups/safe-trusted-ai",
            "https://impact.indiaai.gov.in/working-groups/ai-compute",
            "https://impact.indiaai.gov.in/working-groups/ai-for-all",
            "https://impact.indiaai.gov.in/working-groups/ai-innovation-startups",
            "https://impact.indiaai.gov.in/working-groups/future-of-work",
            "https://impact.indiaai.gov.in/working-groups/indiaai-datasets-platform",
            "https://impact.indiaai.gov.in/working-groups/responsible-ai",
        ],
        "max_pages": 40,
        "priority": 2,
    },
    
    "events_challenges": {
        "name": "Events - Challenges",
        "description": "AI for ALL, AI by HER, YUVAi challenges",
        "seeds": [
            "https://impact.indiaai.gov.in/events/ai-for-all",
            "https://impact.indiaai.gov.in/events/ai-by-her",
            "https://impact.indiaai.gov.in/events/yuvai",
            "https://impact.indiaai.gov.in/events/research-symposium",
            "https://www.impactexpo.indiaai.gov.in/",
            "https://impact.indiaai.gov.in/events/atal-tinkering-labs"
        ],
        "max_pages": 40,
        "priority": 3,
    },
    
    "events_casebook": {
        "name": "Events - Casebook",
        "description": "All 6 casebook domain pages",
        "seeds": [
            "https://impact.indiaai.gov.in/events/casebook",
            "https://impact.indiaai.gov.in/events/casebook/health",
            "https://impact.indiaai.gov.in/events/casebook/education",
            "https://impact.indiaai.gov.in/events/casebook/agriculture",
            "https://impact.indiaai.gov.in/events/casebook/energy",
            "https://impact.indiaai.gov.in/events/casebook/gender",
            "https://impact.indiaai.gov.in/events/casebook/disability",
        ],
        "max_pages": 40,
        "priority": 4,
    },
    
    "pre_summit_events": {
        "name": "Pre-Summit Events",
        "description": "Pre-summit and main summit event listings",
        "seeds": [
            "https://impact.indiaai.gov.in/home/pre-summit-events",
            "https://impact.indiaai.gov.in/home/host-pre-summit-events",
            "https://impact.indiaai.gov.in/home/main-summit-events",
        ],
        "max_pages": 30,
        "priority": 5,
    },
    
    "about_info": {
        "name": "About & Info Pages",
        "description": "Static informational pages",
        "seeds": [
            "https://impact.indiaai.gov.in",
            "https://impact.indiaai.gov.in/about-summit",
            "https://impact.indiaai.gov.in/contact-us",
        ],
        "max_pages": 20,
        "priority": 6,
    },
    
    "pdfs_documents": {
        "name": "PDFs & Documents",
        "description": "All downloadable PDFs and documents",
        "seeds": [
            "https://impact.indiaai.gov.in/IndiaAI_Governance_Guidelines.pdf",
        ],
        "max_pages": 40,
        "priority": 7,
    },
}


def get_section(section_id):
    """Get section configuration by ID."""
    return SECTIONS.get(section_id)


def get_all_sections():
    """Get all sections sorted by priority."""
    return sorted(SECTIONS.items(), key=lambda x: x[1]["priority"])


def get_section_seeds(section_id):
    """Get seed URLs for a specific section."""
    section = SECTIONS.get(section_id)
    return section["seeds"] if section else []


def get_section_max_pages(section_id):
    """Get max pages for a specific section."""
    section = SECTIONS.get(section_id)
    return section["max_pages"] if section else 10


def url_matches_section(url, section_id):
    """
    Check if a URL belongs to a specific section.
    
    Args:
        url: URL to check
        section_id: Section identifier
        
    Returns:
        True if URL matches section patterns, False otherwise
    """
    from urllib.parse import urlparse
    
    path = urlparse(url).path.lower()
    
    # Section-specific URL patterns
    patterns = {
        "agenda": ["/agenda"],
        "working_groups": ["/working-groups"],
        "events_challenges": [
            "/events/ai-for-all",
            "/events/ai-by-her", 
            "/events/yuvai",
            "/events/aboutthechallenge"
        ],
        "events_casebook": [
            "/events/casebook"
        ],
        "pre_summit_events": [
            "/home/pre-summit-events",
            "/home/host-pre-summit-events",
            "/home/main-summit-events"
        ],
        "about_info": [
            "/about-summit",
            "/contact-us"
        ],
        "pdfs_documents": [
            ".pdf"
        ],
    }
    
    # Get patterns for this section
    section_patterns = patterns.get(section_id, [])
    
    # Special case: homepage belongs to about_info
    if section_id == "about_info" and path in ["/", ""]:
        return True
    
    # Check if URL matches any pattern for this section
    for pattern in section_patterns:
        if pattern in path:
            return True
    
    return False
