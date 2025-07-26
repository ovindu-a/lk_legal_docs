#!/usr/bin/env python3
"""
Example usage of the TextExtractionService
"""

from lld.services.text_extraction import TextExtractionService, ExtractionMethod

def main():
    # Initialize the service
    service = TextExtractionService()
    
    # Example URL from the gazette data
    example_url = "https://documents.gov.lk/view/gazettes/2006/3/2006-03-03(I-I)E.pdf"
    
    print("Available extraction methods:", service.get_available_methods())
    print("\n" + "="*50)
    
    # Example 1: Extract using PyPDF method
    print("1. Extracting with PyPDF method:")
    result = service.extract_text_from_url(
        example_url, 
        method=ExtractionMethod.PYPDF
    )
    
    if result["success"]:
        print(f"✓ Success! Method used: {result['method_used']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"First 200 characters: {result['text'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "="*50)
    
    # Example 2: Extract using PyMuPDF method
    print("2. Extracting with PyMuPDF method:")
    result = service.extract_text_from_url(
        example_url, 
        method=ExtractionMethod.PYMUPDF
    )
    
    if result["success"]:
        print(f"✓ Success! Method used: {result['method_used']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"First 200 characters: {result['text'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "="*50)
    
    # Example 3: Extract using combined method (default)
    print("3. Extracting with combined method (default):")
    result = service.extract_text_from_url(example_url)
    
    if result["success"]:
        print(f"✓ Success! Method used: {result['method_used']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"First 200 characters: {result['text'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "="*50)
    
    # Example 4: Save extracted text to file
    print("4. Extracting and saving to file:")
    result = service.extract_text_from_url(
        example_url,
        method=ExtractionMethod.COMBINED,
        save_to_file="extracted_text.txt"
    )
    
    if result["success"]:
        print(f"✓ Success! Text saved to extracted_text.txt")
        print(f"Method used: {result['method_used']}")
    else:
        print(f"✗ Failed: {result['error']}")

if __name__ == "__main__":
    main() 