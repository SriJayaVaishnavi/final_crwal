"""Find and extract PDF links from crawled JSON files."""
import json
import io
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def find_pdfs(output_dir: Path = Path("output")):
    """Scan all JSON files in output directory for PDF links."""
    pdf_links = set()
    
    print(f"Scanning {output_dir} for PDF links...")
    
    # Walk through all directories
    for json_file in output_dir.rglob("*.json"):
        # Skip metrics/log files
        if "metrics" in json_file.name or "frontier" in json_file.name:
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures (consolidated vs individual)
            docs = []
            if "documents" in data:
                docs = data["documents"]
            elif isinstance(data, dict):
                docs = [data]
            elif isinstance(data, list):
                docs = data
                
            for doc in docs:
                # Check outbound links
                if "outbound_links" in doc:
                    for link in doc["outbound_links"]:
                        href = link.get("href", "")
                        if href.lower().endswith(".pdf"):
                            pdf_links.add(href)
                            print(f"Found PDF: {href}")
                            
        except Exception as e:
            # print(f"Error reading {json_file}: {e}")
            pass
            
    print(f"\nTotal unique PDFs found: {len(pdf_links)}")
    
    # Save list to file
    with open("pdf_links.txt", "w", encoding="utf-8") as f:
        for link in sorted(pdf_links):
            f.write(f"{link}\n")
            
    print("PDF list saved to 'pdf_links.txt'")
    return list(pdf_links)

if __name__ == "__main__":
    find_pdfs()
