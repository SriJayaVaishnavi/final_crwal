"""Event extractor for working-group pages and event listings."""
from typing import List, Optional
from bs4 import BeautifulSoup
import hashlib
import re
from .base import BaseExtractor
from models import Event, Entity


class EventExtractor(BaseExtractor):
    """Extract event entities from event listings and working-group pages."""
    
    def extract(self, html: str, markdown: str, url: str) -> List[Entity]:
        """Extract events from page."""
        soup = BeautifulSoup(html, "html.parser")
        entities = []
        
        # Strategy 1: Look for event cards/blocks
        event_cards = self._find_event_cards(soup)
        if event_cards:
            entities.extend(self._extract_from_cards(event_cards, url))
        
        # Strategy 2: Extract from markdown structure
        if not entities:
            entities.extend(self._extract_from_markdown(markdown, url))
            
        return entities
        
    def _find_event_cards(self, soup: BeautifulSoup) -> List:
        """Find event card elements in HTML."""
        cards = []
        
        # Common patterns for event cards
        # 1. Divs with class containing "event", "card", "item"
        for div in soup.find_all("div", class_=re.compile(r"event|card|item", re.I)):
            # Check if it contains event-like content
            text = div.get_text()
            if any(keyword in text.lower() for keyword in ["register", "event", "conclave", "workshop", "meeting"]):
                cards.append(div)
                
        # 2. Article tags
        cards.extend(soup.find_all("article"))
        
        # 3. List items in event sections
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li"):
                text = li.get_text()
                if len(text) > 50 and any(keyword in text.lower() for keyword in ["register", "event", "date"]):
                    cards.append(li)
                    
        return cards
        
    def _extract_from_cards(self, cards: List, url: str) -> List[Event]:
        """Extract event data from card elements."""
        events = []
        
        for card in cards:
            # Extract title
            title_elem = card.find(["h1", "h2", "h3", "h4", "h5", "strong", "b"])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                continue
                
            # Extract text content
            text = card.get_text(separator=" ", strip=True)
            
            # Extract date
            date = self._extract_date_from_text(text)
            
            # Extract location (city, country)
            city, country = self._extract_location(text)
            
            # Extract organizer
            organizer = self._extract_organizer(text)
            
            # Extract registration link
            registration_url = None
            for link in card.find_all("a"):
                link_text = link.get_text().lower()
                if any(keyword in link_text for keyword in ["register", "sign up", "rsvp"]):
                    registration_url = link.get("href")
                    break
                    
            # Extract working group from URL
            working_group = None
            if "working-group" in url:
                parts = url.split("working-groups/")
                if len(parts) > 1:
                    working_group = parts[1].split("/")[0].replace("-", " ").title()
                    
            # Generate entity ID
            entity_id = hashlib.sha256(
                f"{url}_{title}_{date}".encode()
            ).hexdigest()
            
            event = Event(
                entity_id=entity_id,
                source_url=url,
                event_title=self.clean_text(title),
                event_date=date,
                city=city,
                country=country,
                organizer=organizer,
                description=self.clean_text(text[:500]),
                registration_url=registration_url,
                working_group=working_group,
                metadata={"extraction_method": "cards"}
            )
            events.append(event)
            
        return events
        
    def _extract_from_markdown(self, markdown: str, url: str) -> List[Event]:
        """Extract events from markdown structure."""
        events = []
        lines = markdown.split("\n")
        
        current_event = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect event headings
            if line.startswith("#"):
                # Save previous event if exists
                if current_event.get("title"):
                    events.append(self._create_event_from_dict(current_event, url))
                    
                # Start new event
                current_event = {"title": line.lstrip("#").strip()}
            else:
                # Accumulate description
                if "description" not in current_event:
                    current_event["description"] = line
                else:
                    current_event["description"] += " " + line
                    
                # Extract date if found
                if not current_event.get("date"):
                    date = self._extract_date_from_text(line)
                    if date:
                        current_event["date"] = date
                        
        # Save last event
        if current_event.get("title"):
            events.append(self._create_event_from_dict(current_event, url))
            
        return events
        
    def _create_event_from_dict(self, data: dict, url: str) -> Event:
        """Create Event entity from dictionary."""
        entity_id = hashlib.sha256(
            f"{url}_{data.get('title')}_{data.get('date')}".encode()
        ).hexdigest()
        
        return Event(
            entity_id=entity_id,
            source_url=url,
            event_title=self.clean_text(data.get("title")),
            event_date=data.get("date"),
            description=self.clean_text(data.get("description")),
            metadata={"extraction_method": "markdown"}
        )
        
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text using patterns."""
        # Pattern: Month DD, YYYY or DD Month YYYY
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.parse_date(" ".join(match.groups()))
                
        return None
        
    def _extract_location(self, text: str) -> tuple:
        """Extract city and country from text."""
        # Simple pattern: City, Country
        location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)'
        match = re.search(location_pattern, text)
        
        if match:
            return match.group(1), match.group(2)
        return None, None
        
    def _extract_organizer(self, text: str) -> Optional[str]:
        """Extract organizer from text."""
        # Pattern: "by X" or "organized by X"
        organizer_pattern = r'(?:organized\s+)?by\s+([A-Z][^.,;]+)'
        match = re.search(organizer_pattern, text, re.IGNORECASE)
        
        if match:
            return self.clean_text(match.group(1))
        return None
