"""Configuration management for IndiaAI crawler."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class CrawlerConfig(BaseSettings):
    """Main crawler configuration."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Concurrency settings
    max_concurrent_requests: int = Field(default=5, description="Max concurrent crawl requests")
    max_depth: int = Field(default=5, description="Maximum crawl depth")
    max_pages_per_run: int = Field(default=1000, description="Max pages to crawl per run")
    max_pages_per_section: int = Field(default=150, description="Max pages per section")
    request_delay_seconds: float = Field(default=2.0, description="Delay between request batches")
    
    # Timeout settings
    page_timeout_ms: int = Field(default=60000, description="Page load timeout in milliseconds")
    wait_for_selector_timeout_ms: int = Field(default=10000, description="Selector wait timeout")
    
    # User agent
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="Browser user agent"
    )
    
    # Domain scope
    allowed_domain: str = Field(default="impact.indiaai.gov.in", description="Allowed crawl domain")
    
    # Anti-bot settings
    enable_stealth: bool = Field(default=True, description="Enable stealth mode")
    enable_undetected: bool = Field(default=True, description="Enable undetected browser mode")
    proxy_url: Optional[str] = Field(default=None, description="Proxy URL (optional)")
    
    # Output settings
    output_dir: Path = Field(default=Path("./output"), description="Output directory")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Chunking settings
    chunk_size_tokens: int = Field(default=800, description="Target chunk size in tokens")
    chunk_overlap_percent: int = Field(default=12, description="Chunk overlap percentage")
    min_chunk_size_tokens: int = Field(default=100, description="Minimum chunk size")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Max retry attempts per URL")
    retry_backoff_factor: float = Field(default=2.0, description="Exponential backoff factor")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "documents").mkdir(exist_ok=True)
        (self.output_dir / "chunks").mkdir(exist_ok=True)
        (self.output_dir / "pdfs").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)


# Global config instance
config = CrawlerConfig()
