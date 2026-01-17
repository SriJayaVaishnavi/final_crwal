"""Export frontier database to JSON format."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime


def export_frontier_to_json(db_path: Path = Path("frontier.db"), output_path: Path = None):
    """
    Export all URLs from frontier database to JSON file.
    
    Args:
        db_path: Path to frontier.db SQLite database
        output_path: Path to output JSON file (default: frontier_export.json)
    """
    if output_path is None:
        output_path = Path("output") / f"frontier_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    
    # Fetch all URLs
    cursor.execute("""
        SELECT 
            url_hash,
            url,
            canonical_url,
            depth,
            parent_url,
            priority,
            status,
            attempts,
            last_crawled,
            etag,
            last_modified,
            error_message,
            created_at
        FROM urls
        ORDER BY priority DESC, created_at ASC
    """)
    
    # Convert to list of dictionaries
    urls = []
    for row in cursor.fetchall():
        urls.append({
            "url_hash": row["url_hash"],
            "url": row["url"],
            "canonical_url": row["canonical_url"],
            "depth": row["depth"],
            "parent_url": row["parent_url"],
            "priority": row["priority"],
            "status": row["status"],
            "attempts": row["attempts"],
            "last_crawled": row["last_crawled"],
            "etag": row["etag"],
            "last_modified": row["last_modified"],
            "error_message": row["error_message"],
            "created_at": row["created_at"]
        })
    
    # Get statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
        FROM urls
    """)
    
    stats_row = cursor.fetchone()
    stats = {
        "total": stats_row["total"],
        "pending": stats_row["pending"] or 0,
        "success": stats_row["success"] or 0,
        "failed": stats_row["failed"] or 0,
        "in_progress": stats_row["in_progress"] or 0
    }
    
    conn.close()
    
    # Create export data
    export_data = {
        "export_timestamp": datetime.utcnow().isoformat() + "Z",
        "database_path": str(db_path),
        "statistics": stats,
        "urls": urls
    }
    
    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(urls)} URLs to {output_path}")
    print(f"\nStatistics:")
    print(f"  Total URLs: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Success: {stats['success']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  In Progress: {stats['in_progress']}")
    
    return output_path


if __name__ == "__main__":
    export_frontier_to_json()
