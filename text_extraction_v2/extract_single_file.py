#!/usr/bin/env python3
"""
Simple example to extract text from a single PDF file using Gemini
Supports both local files and URLs
"""

import os
import sys
from text_extraction_v2.service import TextExtractionService
from text_extraction_v2.base import ExtractionMethod

def extract_text_from_pdf(pdf_path_or_url, output_file=None):
    """
    Extract text from a PDF file or URL using Gemini
    
    Args:
        pdf_path_or_url: Path to local PDF file or URL
        output_file: Optional path to save extracted text
    """
    # Initialize service
    service = TextExtractionService()
    
    # Check if it's a URL
    is_url = pdf_path_or_url.startswith(('http://', 'https://'))
    
    print(f"Processing: {pdf_path_or_url}")
    print(f"Type: {'URL' if is_url else 'Local file'}")
    print("-" * 80)
    
    try:
        if is_url:
            # Use GEMINI_URL for direct URL extraction
            result = service.extract_from_url(
                url=pdf_path_or_url,
                method=ExtractionMethod.GEMINI_URL,
                save_to_file=output_file
            )
        else:
            # Use regular GEMINI for local files
            result = service.extract_from_file(
                pdf_path=pdf_path_or_url,
                method=ExtractionMethod.GEMINI,
                save_to_file=output_file
            )
        
        if result.success:
            print("✓ Extraction successful!")
            print(f"  Method used: {result.method_used}")
            print(f"  Extraction time: {result.extraction_time:.2f} seconds")
            print(f"  Text length: {len(result.text)} characters")
            
            if output_file:
                print(f"  Saved to: {output_file}")
            
            print("\n--- EXTRACTED TEXT PREVIEW (first 1000 chars) ---")
            print(result.text[:1000])
            if len(result.text) > 1000:
                print("\n... (truncated)")
            
            return result.text
            
        else:
            print(f"✗ Extraction failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def main():
    # Check if API key is set
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Example 1: Extract from a URL
    print("=" * 80)
    print("EXAMPLE 1: Extracting from URL")
    print("=" * 80)
    
    url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    extract_text_from_pdf(url, "extracted_from_url.txt")
    
    print("\n\n")
    
    # Example 2: Extract from a local file (if you have one)
    print("=" * 80)
    print("EXAMPLE 2: Extracting from local file")
    print("=" * 80)
    
    # Replace with your actual PDF path
    local_pdf = "sample.pdf"
    
    if os.path.exists(local_pdf):
        extract_text_from_pdf(local_pdf, "extracted_from_local.txt")
    else:
        print(f"Local file '{local_pdf}' not found. Skipping local file example.")
        print("To test with a local file, place a PDF in the current directory")
    
    # Example 3: Using command line argument
    if len(sys.argv) > 1:
        print("\n\n")
        print("=" * 80)
        print("EXTRACTING FROM COMMAND LINE ARGUMENT")
        print("=" * 80)
        
        pdf_input = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        extract_text_from_pdf(pdf_input, output_file)


if __name__ == "__main__":
    # If run with arguments, use those. Otherwise run examples
    if len(sys.argv) > 1:
        # Usage: python extract_single_file.py <pdf_path_or_url> [output_file]
        main()
    else:
        print("Usage: python extract_single_file.py <pdf_path_or_url> [output_file]")
        print("\nRunning examples...")
        main()