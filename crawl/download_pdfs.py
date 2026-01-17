"""Download PDFs from a list of URLs."""
import os
import sys
import io
import requests
from pathlib import Path
from urllib.parse import unquote

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def download_pdfs(links_file: str = "pdf_links.txt", output_dir: Path = Path("output/pdfs")):
    """Download PDFs from the links file."""
    if not os.path.exists(links_file):
        print(f"File {links_file} not found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(links_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"Found {len(urls)} PDFs to download.")
    
    for url in urls:
        try:
            filename = unquote(url.split("/")[-1])
            # Sanitize filename
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-'))
            save_path = output_dir / filename
            
            print(f"Downloading: {filename}...")
            
            response = requests.get(url, stream=True, verify=False) # verify=False because of potential SSL issues with govt sites
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✓ Saved to {save_path}")
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    download_pdfs()
