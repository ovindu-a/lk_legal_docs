#!/usr/bin/env python3
"""
Example of using the Gemini URL extractor to extract text directly from online PDFs
"""

import os
from text_extraction_v2.service import TextExtractionService
from text_extraction_v2.base import ExtractionMethod

def main():
    # Initialize service with Gemini API key
    # Make sure GOOGLE_API_KEY environment variable is set
    service = TextExtractionService()
    
    # Example PDF URL
    pdf_url = "https://discovery.ucl.ac.uk/id/eprint/10089234/1/343019_3_art_0_py4t4l_convrt.pdf"
    
    print(f"Extracting text from: {pdf_url}")
    print("-" * 80)
    
    # Method 1: Using the service's extract_from_url with GEMINI_URL method
    # This uses direct URL extraction without downloading to a temp file
    result = service.extract_from_url(
        url=pdf_url,
        method=ExtractionMethod.GEMINI_URL,
        prompt="Extract all text content from this document, preserving the structure."
    )
    
    if result.success:
        print("Extraction successful!")
        print(f"Method used: {result.method_used}")
        print(f"Extraction time: {result.extraction_time:.2f} seconds")
        print(f"Text length: {len(result.text)} characters")
        print("\nFirst 500 characters:")
        print(result.text[:500])
        print("...")
    else:
        print(f"Extraction failed: {result.error}")
    
    print("\n" + "-" * 80)
    
    # Method 2: Using the extractor directly for more control
    from text_extraction_v2.extractors import GeminiURLExtractor
    
    try:
        # Create extractor instance
        extractor = GeminiURLExtractor()
        
        # Extract with custom prompt
        result2 = extractor.extract_from_url(
            url=pdf_url,
            prompt="Summarize the key points of this document in bullet points.",
            include_formatting=False
        )
        
        if result2.success:
            print("Summary extraction successful!")
            print("\nDocument Summary:")
            print(result2.text)
        else:
            print(f"Summary extraction failed: {result2.error}")
            
    except Exception as e:
        print(f"Error creating extractor: {e}")
        print("Make sure to install required dependencies: pip install google-genai httpx")

if __name__ == "__main__":
    main()