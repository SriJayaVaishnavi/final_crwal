"""Agenda item extractor."""
from typing import List
from bs4 import BeautifulSoup
import hashlib
from .base import BaseExtractor
from models import AgendaItem, Entity


class AgendaExtractor(BaseExtractor):
    """Extract agenda items from agenda pages."""
    
    def extract(self, html: str, markdown: str, url: str) -> List[Entity]:
        """Extract agenda items from page."""
        soup = BeautifulSoup(html, "html.parser")
        entities = []
        
        # Strategy 1: Look for structured agenda blocks
        # Common patterns: day sections with time slots
        
        # Find day sections (h2, h3 with "Day" in text)
        day_sections = []
        for heading in soup.find_all(["h2", "h3"]):
            heading_text = heading.get_text(strip=True)
            if "day" in heading_text.lower():
                day_sections.append((heading, heading_text))
                
        if day_sections:
            entities.extend(self._extract_from_day_sections(day_sections, url))
        else:
            # Fallback: Extract from markdown structure
            entities.extend(self._extract_from_markdown(markdown, url))
            
        return entities
        
    def _extract_from_day_sections(self, day_sections: List, url: str) -> List[AgendaItem]:
        """Extract agenda items from day section headings."""
        items = []
        
        for heading, day_name in day_sections:
            # Get all content until next day section
            current_items = []
            
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h2", "h3"] and "day" in sibling.get_text().lower():
                    break
                    
                # Look for time-based entries
                text = sibling.get_text(strip=True)
                if not text:
                    continue
                    
                # Try to parse time-based entries
                # Pattern: HH:MM - HH:MM: Title
                import re
                time_pattern = r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\s*[:-]?\s*(.+)'
                match = re.match(time_pattern, text)
                
                if match:
                    start_time, end_time, title = match.groups()
                    
                    # Generate entity ID
                    entity_id = hashlib.sha256(
                        f"{url}_{day_name}_{start_time}_{title}".encode()
                    ).hexdigest()
                    
                    item = AgendaItem(
                        entity_id=entity_id,
                        source_url=url,
                        title=self.clean_text(title),
                        day_name=day_name,
                        start_time=start_time,
                        end_time=end_time,
                        page_section=day_name,
                        metadata={"extraction_method": "day_sections"}
                    )
                    items.append(item)
                else:
                    # No time pattern, treat as description or standalone item
                    if len(text) > 20:  # Meaningful content
                        entity_id = hashlib.sha256(
                            f"{url}_{day_name}_{text[:50]}".encode()
                        ).hexdigest()
                        
                        item = AgendaItem(
                            entity_id=entity_id,
                            source_url=url,
                            title=self.clean_text(text[:200]),
                            description=self.clean_text(text) if len(text) > 200 else None,
                            day_name=day_name,
                            page_section=day_name,
                            metadata={"extraction_method": "day_sections"}
                        )
                        items.append(item)
                        
        return items
        
    def _extract_from_markdown(self, markdown: str, url: str) -> List[AgendaItem]:
        """Extract agenda items from markdown structure."""
        items = []
        lines = markdown.split("\n")
        
        current_day = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect day headings
            if line.startswith("#") and "day" in line.lower():
                current_day = line.lstrip("#").strip()
                continue
                
            # Detect time-based entries
            import re
            time_pattern = r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})\s*[:-]?\s*(.+)'
            match = re.match(time_pattern, line)
            
            if match:
                start_time, end_time, title = match.groups()
                
                entity_id = hashlib.sha256(
                    f"{url}_{current_day}_{start_time}_{title}".encode()
                ).hexdigest()
                
                item = AgendaItem(
                    entity_id=entity_id,
                    source_url=url,
                    title=self.clean_text(title),
                    day_name=current_day,
                    start_time=start_time,
                    end_time=end_time,
                    page_section=current_day,
                    metadata={"extraction_method": "markdown"}
                )
                items.append(item)
                
        return items
