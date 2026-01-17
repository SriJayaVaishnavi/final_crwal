"""Structured logging for the crawler."""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from config import config


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra context if available
        if hasattr(record, "context"):
            log_data["context"] = record.context
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (JSON)
    log_dir = config.output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "crawler.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(log_dir / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    return logger


class MetricsLogger:
    """Metrics tracking and logging."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "pages_attempted": 0,
            "pages_succeeded": 0,
            "pages_failed": 0,
            "pdfs_processed": 0,
            "entities_extracted": 0,
            "chunks_created": 0,
            "duplicates_filtered": 0,
            "total_crawl_time_seconds": 0,
            "avg_page_time_seconds": 0,
            "errors": [],
        }
        self.logger = setup_logger("metrics")
        
    def increment(self, metric: str, value: int = 1):
        """Increment a metric."""
        if metric in self.metrics:
            self.metrics[metric] += value
            
    def add_error(self, url: str, error: str):
        """Add an error record."""
        self.metrics["errors"].append({
            "url": url,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    def save(self):
        """Save metrics to file."""
        metrics_file = config.output_dir / "logs" / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
        self.logger.info(f"Metrics saved to {metrics_file}")
        
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if self.metrics["pages_attempted"] > 0:
            self.metrics["success_rate"] = (
                self.metrics["pages_succeeded"] / self.metrics["pages_attempted"]
            )
        return self.metrics


# Global metrics instance
metrics = MetricsLogger()
