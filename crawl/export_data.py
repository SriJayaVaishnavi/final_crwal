"""Export all scraped data to a single consolidated JSON file."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a single JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def export_all_data(output_dir: Path = Path("output"), export_filename: str = None):
    """
    Export all scraped data to a single consolidated JSON file.
    
    Args:
        output_dir: Directory containing scraped data
        export_filename: Name of output file (default: scraped_data_TIMESTAMP.json)
    """
    if export_filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f"scraped_data_{timestamp}.json"
    
    export_path = output_dir / export_filename
    
    # Collect all documents
    documents_dir = output_dir / "documents"
    documents = []
    
    if documents_dir.exists():
        print(f"Loading documents from {documents_dir}...")
        for doc_file in documents_dir.glob("*.json"):
            doc_data = load_json_file(doc_file)
            if doc_data:
                documents.append(doc_data)
        print(f"  Loaded {len(documents)} documents")
    
    # Collect all chunks
    chunks_dir = output_dir / "chunks"
    chunks = []
    
    if chunks_dir.exists():
        print(f"Loading chunks from {chunks_dir}...")
        for chunk_file in chunks_dir.glob("*.json"):
            chunk_data = load_json_file(chunk_file)
            if chunk_data:
                chunks.append(chunk_data)
        print(f"  Loaded {len(chunks)} chunks")
    
    # Collect PDF metadata
    pdfs_dir = output_dir / "pdfs"
    pdfs = []
    
    if pdfs_dir.exists():
        print(f"Loading PDF metadata from {pdfs_dir}...")
        for pdf_meta in pdfs_dir.glob("*.json"):
            pdf_data = load_json_file(pdf_meta)
            if pdf_data:
                pdfs.append(pdf_data)
        print(f"  Loaded {len(pdfs)} PDF metadata files")
    
    # Create consolidated export
    export_data = {
        "export_metadata": {
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_documents": len(documents),
            "total_chunks": len(chunks),
            "total_pdfs": len(pdfs),
            "source_directory": str(output_dir.absolute())
        },
        "documents": documents,
        "chunks": chunks,
        "pdfs": pdfs
    }
    
    # Write to JSON file
    print(f"\nWriting consolidated data to {export_path}...")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    file_size_mb = export_path.stat().st_size / (1024 * 1024)
    
    print(f"\n{'='*60}")
    print(f"Export Complete!")
    print(f"{'='*60}")
    print(f"File: {export_path.absolute()}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"\nContents:")
    print(f"  - Documents: {len(documents)}")
    print(f"  - Chunks: {len(chunks)}")
    print(f"  - PDFs: {len(pdfs)}")
    print(f"{'='*60}")
    
    return export_path


if __name__ == "__main__":
    # Export with default settings
    export_all_data()
