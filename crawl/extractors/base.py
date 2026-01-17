"""Base extractor interface and utilities."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import re
from datetime import datetime
from models import Entity


class BaseExtractor(ABC):
    """Abstract base class for content extractors."""
    
    @abstractmethod
    def extract(self, html: str, markdown: str, url: str) -> List[Entity]:
        """
        Extract entities from page content.
        
        Args:
            html: Raw HTML content
            markdown: Cleaned markdown (fit-markdown preferred)
            url: Source URL
            
        Returns:
            List of extracted entities
        """
        pass
        
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text."""
        if not text:
            return None
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove HTML artifacts
        text = re.sub(r'<[^>]+>', '', text)
        
        return text if text else None
        
    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse date string to ISO-8601 format.
        
        Handles common formats:
        - December 11, 2025
        - 11-12-2025
        - 2025-12-11
        """
        if not date_str:
            return None
            
        date_str = self.clean_text(date_str)
        if not date_str:
            return None
            
        # Try common formats
        formats = [
            "%B %d, %Y",      # December 11, 2025
            "%d-%m-%Y",       # 11-12-2025
            "%Y-%m-%d",       # 2025-12-11
            "%d/%m/%Y",       # 11/12/2025
            "%m/%d/%Y",       # 12/11/2025
            "%d %B %Y",       # 11 December 2025
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue
                
        # If no format matches, return original
        return date_str
        
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract common metadata from HTML."""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content
                
        return metadata
        
    def extract_section_from_heading(self, soup: BeautifulSoup, heading_text: str) -> Optional[str]:
        """Extract content under a specific heading."""
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            if heading_text.lower() in heading.get_text().lower():
                # Get all siblings until next heading
                content = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ["h1", "h2", "h3", "h4"]:
                        break
                    content.append(sibling.get_text(strip=True))
                return " ".join(content)
        return None
