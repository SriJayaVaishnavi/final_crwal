"""URL frontier with SQLite-backed priority queue."""
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path
from config import config
from logger import setup_logger
from url_utils import canonicalize_url, get_url_priority


logger = setup_logger("frontier")


class URLFrontier:
    """SQLite-backed URL frontier for crawl queue management."""
    
    def __init__(self, db_path: Path = Path("frontier.db")):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                canonical_url TEXT NOT NULL,
                depth INTEGER NOT NULL,
                parent_url TEXT,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_crawled TEXT,
                etag TEXT,
                last_modified TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority 
            ON urls(status, priority DESC, created_at)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Frontier database initialized at {self.db_path}")
        
    def _url_hash(self, url: str) -> str:
        """Generate SHA256 hash of canonical URL."""
        canonical = canonicalize_url(url)
        return hashlib.sha256(canonical.encode()).hexdigest()
        
    def enqueue(self, url: str, depth: int = 0, parent_url: Optional[str] = None) -> bool:
        """
        Add URL to frontier if not already present.
        
        Returns:
            True if URL was added, False if already exists
        """
        canonical = canonicalize_url(url)
        url_hash = self._url_hash(url)
        priority = get_url_priority(canonical)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO urls (url_hash, url, canonical_url, depth, parent_url, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                url_hash,
                url,
                canonical,
                depth,
                parent_url,
                priority,
                datetime.utcnow().isoformat() + "Z"
            ))
            conn.commit()
            logger.debug(f"Enqueued: {canonical} (depth={depth}, priority={priority})")
            return True
        except sqlite3.IntegrityError:
            # URL already exists
            return False
        finally:
            conn.close()
            
    def dequeue(self) -> Optional[Tuple[str, int, str]]:
        """
        Get next URL to crawl (highest priority, oldest first).
        
        Returns:
            (url, depth, url_hash) or None if queue is empty
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT canonical_url, depth, url_hash
            FROM urls
            WHERE status = 'pending' AND attempts < ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """, (config.max_retries,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            url, depth, url_hash = result
            # Mark as in-progress
            self._update_status(url_hash, "in_progress")
            return (url, depth, url_hash)
        return None
        
    def mark_success(self, url_hash: str, etag: Optional[str] = None, last_modified: Optional[str] = None):
        """Mark URL as successfully crawled."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE urls
            SET status = 'success',
                last_crawled = ?,
                etag = ?,
                last_modified = ?
            WHERE url_hash = ?
        """, (
            datetime.utcnow().isoformat() + "Z",
            etag,
            last_modified,
            url_hash
        ))
        
        conn.commit()
        conn.close()
        
    def mark_failure(self, url_hash: str, error_message: str):
        """Mark URL as failed and increment attempts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE urls
            SET status = 'failed',
                attempts = attempts + 1,
                error_message = ?,
                last_crawled = ?
            WHERE url_hash = ?
        """, (
            error_message,
            datetime.utcnow().isoformat() + "Z",
            url_hash
        ))
        
        conn.commit()
        conn.close()
        
    def _update_status(self, url_hash: str, status: str):
        """Update URL status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE urls SET status = ? WHERE url_hash = ?
        """, (status, url_hash))
        
        conn.commit()
        conn.close()
        
    def get_stats(self) -> dict:
        """Get frontier statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
            FROM urls
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total": row[0],
            "pending": row[1] or 0,
            "success": row[2] or 0,
            "failed": row[3] or 0,
            "in_progress": row[4] or 0
        }
        
    def reset_in_progress(self):
        """Reset in-progress URLs to pending (for crash recovery)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE urls SET status = 'pending' WHERE status = 'in_progress'
        """)
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if count > 0:
            logger.info(f"Reset {count} in-progress URLs to pending")
