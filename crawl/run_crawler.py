"""Wrapper script to run crawler with proper UTF-8 encoding on Windows."""
import sys
import os

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # Set console code page to UTF-8
    os.system('chcp 65001 > nul')

# Now import and run main
from main import main

if __name__ == "__main__":
    main()
