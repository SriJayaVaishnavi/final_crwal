"""Comprehensive seed URLs for IndiaAI Impact crawl."""

# Base URL
BASE_URL = "https://impact.indiaai.gov.in"

# Comprehensive seed list based on checklist
SEED_URLS = [
    # Homepage
    f"{BASE_URL}",
    
    # Main sections
    f"{BASE_URL}/agenda",
    f"{BASE_URL}/contact-us",
    f"{BASE_URL}/about-summit",
    
    # Pre-summit events
    f"{BASE_URL}/home/pre-summit-events",
    f"{BASE_URL}/home/host-pre-summit-events",
    f"{BASE_URL}/home/main-summit-events",
    
    # Working Groups (Chakras)
    f"{BASE_URL}/working-groups",
    f"{BASE_URL}/working-groups/safe-trusted-ai",
    f"{BASE_URL}/working-groups/ai-compute",
    f"{BASE_URL}/working-groups/ai-for-all",
    f"{BASE_URL}/working-groups/ai-innovation-startups",
    f"{BASE_URL}/working-groups/future-of-work",
    f"{BASE_URL}/working-groups/indiaai-datasets-platform",
    f"{BASE_URL}/working-groups/responsible-ai",
    
    # Events and Challenges
    f"{BASE_URL}/events",
    f"{BASE_URL}/events/ai-for-all",
    f"{BASE_URL}/events/ai-by-her",
    f"{BASE_URL}/events/yuvai",
    f"{BASE_URL}/events/casebook",
    
    # Casebook specific pages
    f"{BASE_URL}/events/casebook/health",
    f"{BASE_URL}/events/casebook/education",
    f"{BASE_URL}/events/casebook/agriculture",
    f"{BASE_URL}/events/casebook/energy",
    f"{BASE_URL}/events/casebook/gender",
    f"{BASE_URL}/events/casebook/disability",
    
    # Known PDFs and documents
    f"{BASE_URL}/IndiaAI_Governance_Guidelines.pdf",
    f"{BASE_URL}/events/aboutTheChallenge",
    
    # Expo subdomain (if accessible)
    "https://impactexpo.indiaai.gov.in",
]

# Additional patterns to discover
URL_PATTERNS = [
    "/events/*",
    "/working-groups/*",
    "/assets/*.pdf",
    "/events/compendiums/**/*.pdf",
]

def get_all_seeds():
    """Return all seed URLs."""
    return SEED_URLS

def get_high_priority_seeds():
    """Return high-priority seeds for initial crawl."""
    return [
        f"{BASE_URL}",
        f"{BASE_URL}/agenda",
        f"{BASE_URL}/working-groups",
        f"{BASE_URL}/events",
        f"{BASE_URL}/home/pre-summit-events",
    ]
