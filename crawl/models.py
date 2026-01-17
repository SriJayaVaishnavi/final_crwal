"""Data models for IndiaAI crawler."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """Content type enumeration."""
    AGENDA_ITEM = "agenda_item"
    EVENT = "event"
    EXHIBITION = "exhibition"
    INITIATIVE_DOC = "initiative_doc"
    NEWS = "news"
    WORKING_GROUP_PAGE = "working_group_page"
    GENERIC_PAGE = "generic_page"


class LinkType(str, Enum):
    """Link type classification."""
    REGISTRATION = "registration"
    EOI = "eoi"
    DOWNLOAD = "download"
    NAVIGATION = "navigation"
    EXTERNAL = "external"


class OutboundLink(BaseModel):
    """Outbound link metadata."""
    href: str
    text: str
    link_type: LinkType = LinkType.NAVIGATION


class Entity(BaseModel):
    """Base entity model."""
    entity_type: str
    entity_id: str
    source_url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgendaItem(Entity):
    """Agenda item entity."""
    entity_type: Literal["agenda_item"] = "agenda_item"
    title: str
    date: Optional[str] = None
    day_name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    page_section: Optional[str] = None


class Event(Entity):
    """Event entity."""
    entity_type: Literal["event"] = "event"
    event_title: str
    event_date: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    format: Optional[str] = None  # physical/hybrid/virtual
    organizer: Optional[str] = None
    description: Optional[str] = None
    registration_url: Optional[str] = None
    working_group: Optional[str] = None


class Exhibition(Entity):
    """Exhibition entity."""
    entity_type: Literal["exhibition"] = "exhibition"
    exhibition_name: str
    date_range: Optional[str] = None
    venue: Optional[str] = None
    summary: Optional[str] = None
    themes: List[str] = Field(default_factory=list)
    visitor_profile: Optional[str] = None
    cta_links: List[OutboundLink] = Field(default_factory=list)
    contact_info: Optional[str] = None


class Initiative(Entity):
    """Initiative document entity."""
    entity_type: Literal["initiative_doc"] = "initiative_doc"
    initiative_name: str
    initiative_type: Optional[str] = None  # challenge/guide/call
    eligibility: Optional[str] = None
    deadlines: List[str] = Field(default_factory=list)
    prizes: Optional[str] = None
    submission_process: Optional[str] = None
    contacts: Optional[str] = None


class NewsArticle(Entity):
    """News article entity."""
    entity_type: Literal["news"] = "news"
    headline: str
    publication_date: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    body: str
    tags: List[str] = Field(default_factory=list)


class PageDocument(BaseModel):
    """Top-level page document."""
    doc_id: str
    source_url: str
    canonical_url: str
    content_type: ContentType
    title: Optional[str] = None
    section_path: List[str] = Field(default_factory=list)
    published_date: Optional[str] = None
    event_date: Optional[str] = None
    crawl_timestamp_utc: str
    raw_text: str
    entities: List[Entity] = Field(default_factory=list)
    outbound_links: List[OutboundLink] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Chunk(BaseModel):
    """RAG-ready chunk."""
    chunk_id: str
    doc_id: str
    source_url: str
    content_type: str
    section_path: List[str] = Field(default_factory=list)
    text: str
    anchor_heading: Optional[str] = None
    position: int
    event_date: Optional[str] = None
    published_date: Optional[str] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    entity_type: Optional[str] = None
    working_group: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CrawlResult(BaseModel):
    """Crawl result metadata."""
    url: str
    status_code: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    crawl_timestamp: str
    page_document: Optional[PageDocument] = None
    chunks: List[Chunk] = Field(default_factory=list)
