"""Combine all crawled JSON files into a single master dataset."""
import json
import io
import sys
from pathlib import Path
from datetime import datetime

# Force UTF-8 encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def combine_data(output_dir: Path = Path("output"), output_file: str = "indiaai_impact_complete_data.json"):
    """Combine all crawled data into one file."""
    print(f"Scanning {output_dir} for data files...")
    
    master_data = {
        "metadata": {
            "title": "IndiaAI Impact Summit Website Dump",
            "generated_at": datetime.now().isoformat(),
            "source_domain": "impact.indiaai.gov.in",
        },
        "stats": {
            "total_pages": 0,
            "sections_covered": [],
        },
        "documents": []
    }
    
    sections_found = set()
    
    # Walk through all directories
    for json_file in output_dir.rglob("*.json"):
        # Skip logs, metrics, frontier files, and previous exports
        if any(x in json_file.name.lower() for x in ["metrics", "frontier", "complete_data", "scraped_data"]):
            continue
            
        # Only include section_slug_timestamp.json pattern usually
        # But we'll try to read everything that looks like a document export
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Normalize different formats we used
            docs_to_add = []
            
            if "documents" in data:
                docs = data["documents"]
                if isinstance(docs, list):
                    docs_to_add = docs
                else:
                    docs_to_add = [docs]
            elif isinstance(data, dict) and "url" in data and "raw_text" in data:
                 # Single doc structure
                 docs_to_add = [data]
            
            # Add valid documents
            for doc in docs_to_add:
                # Add source filename for traceability
                doc["_source_file"] = json_file.name
                
                # Deduplicate based on URL if possible (optional)
                master_data["documents"].append(doc)
                
                # Track sections
                section = json_file.parent.name
                sections_found.add(section)
                
                print(f"✓ Added: {json_file.name} ({len(docs_to_add)} docs)")
                
        except Exception as e:
            # print(f"Skipping {json_file.name}: {e}")
            pass
            
    # Update stats
    master_data["stats"]["total_pages"] = len(master_data["documents"])
    master_data["stats"]["sections_covered"] = sorted(list(sections_found))
    
    # Save master file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n" + "="*50)
    print(f"COMPLETED! Combined {master_data['stats']['total_pages']} pages.")
    print(f"Sections covered: {', '.join(master_data['stats']['sections_covered'])}")
    print(f"Saved to: {output_file}")
    print(f"="*50)

if __name__ == "__main__":
    Combine_data() if "combine" in sys.argv else combine_data()
