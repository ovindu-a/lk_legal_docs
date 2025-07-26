#!/usr/bin/env python3
"""
Quick and simple script to extract text from a single PDF using Gemini
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from text_extraction_v2
sys.path.insert(0, str(Path(__file__).parent.parent))

from text_extraction_v2.extractors import GeminiURLExtractor

# Make sure your API key is set
if not os.environ.get('GOOGLE_API_KEY'):
    print("Please set GOOGLE_API_KEY environment variable")
    exit(1)

# Initialize the extractor
extractor = GeminiURLExtractor()

# Example with a URL
pdf_url = "https://documents.gov.lk/view/gazettes/2006/6/2006-06-23(I-IIB)E.pdf"

print(f"Extracting from: {pdf_url}")
result = extractor.extract_from_url(pdf_url)

if result.success:
    print("\n--- EXTRACTED TEXT ---")
    print(result.text)
    
    # Save to file
    with open("extracted_text.txt", "w") as f:
        f.write(result.text)
    print("\nText saved to: extracted_text.txt")
else:
    print(f"Error: {result.error}")