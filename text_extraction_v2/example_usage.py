#!/usr/bin/env python3
"""
Example usage of the TextExtractionService

This script demonstrates various ways to use the text extraction service
with different methods and options.
"""

import logging
from service import TextExtractionService
from base import ExtractionMethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_basic_extraction():
    """Basic text extraction from URL"""
    print("\n=== Basic Extraction from URL ===")
    
    service = TextExtractionService()
    
    # Example PDF URL (replace with actual URL)
    pdf_url = "https://example.com/document.pdf"
    
    # Extract using default method (Combined)
    result = service.extract_from_url(pdf_url)
    
    if result.success:
        print(f"Extraction successful using {result.method_used}")
        print(f"Extracted {len(result.text)} characters from {result.pages} pages")
        print(f"Extraction took {result.extraction_time:.2f} seconds")
        print("\nFirst 500 characters:")
        print(result.text[:500])
    else:
        print(f"Extraction failed: {result.error}")


def example_specific_method():
    """Extract using a specific method"""
    print("\n=== Extraction with Specific Method ===")
    
    service = TextExtractionService()
    pdf_path = "/path/to/local/document.pdf"
    
    # Try different methods
    methods = [
        ExtractionMethod.PYPDF2,
        ExtractionMethod.PDFPLUMBER,
        ExtractionMethod.PYTESSERACT
    ]
    
    for method in methods:
        print(f"\nTrying {method.value}...")
        result = service.extract_from_file(pdf_path, method=method)
        
        if result.success:
            print(f"Success! Extracted {len(result.text)} characters")
            print(f"Features: {service.get_method_features(method)}")
        else:
            print(f"Failed: {result.error}")


def example_with_options():
    """Extract with specific options"""
    print("\n=== Extraction with Custom Options ===")
    
    service = TextExtractionService()
    pdf_path = "/path/to/local/document.pdf"
    
    # PDFPlumber with table extraction
    print("\nPDFPlumber with table extraction:")
    result = service.extract_from_file(
        pdf_path,
        method=ExtractionMethod.PDFPLUMBER,
        extract_tables=True,
        layout=True
    )
    
    if result.success:
        print(f"Extracted with tables: {result.metadata.get('tables_extracted', 0)} tables found")
    
    # OCR with specific language
    print("\nOCR extraction with German language:")
    result = service.extract_from_file(
        pdf_path,
        method=ExtractionMethod.PYTESSERACT,
        language='deu',  # German
        dpi=400,  # Higher DPI for better quality
        preprocess=True
    )
    
    if result.success:
        print(f"OCR extraction completed with language: {result.metadata.get('language')}")


def example_save_to_file():
    """Extract and save to file"""
    print("\n=== Extract and Save to File ===")
    
    service = TextExtractionService()
    pdf_url = "https://example.com/document.pdf"
    
    # Extract and save
    result = service.extract_from_url(
        pdf_url,
        method=ExtractionMethod.COMBINED,
        save_to_file="extracted_text.txt"
    )
    
    if result.success:
        print(f"Text saved to: {result.metadata.get('saved_to')}")


def example_batch_extraction():
    """Extract from multiple PDFs"""
    print("\n=== Batch Extraction ===")
    
    service = TextExtractionService()
    
    pdf_files = [
        "/path/to/document1.pdf",
        "/path/to/document2.pdf",
        "/path/to/document3.pdf"
    ]
    
    # Batch extract with saving
    results = service.batch_extract(
        pdf_files,
        method=ExtractionMethod.COMBINED,
        save_directory="/path/to/output"
    )
    
    # Process results
    for pdf_path, result in results.items():
        if result.success:
            print(f"✓ {pdf_path}: {len(result.text)} characters extracted")
        else:
            print(f"✗ {pdf_path}: {result.error}")


def example_custom_extractor():
    """Register and use a custom extractor"""
    print("\n=== Custom Extractor ===")
    
    from base import BaseExtractor, ExtractionResult
    
    class SimpleExtractor(BaseExtractor):
        def get_name(self):
            return "Simple"
        
        def get_supported_features(self):
            return ["basic_extraction"]
        
        def extract_text(self, pdf_path, **kwargs):
            # Simplified extraction logic
            return ExtractionResult(
                success=True,
                text="This is a simple extractor demo",
                method_used=self.get_name()
            )
    
    service = TextExtractionService()
    
    # Register custom extractor
    service.register_custom_extractor("simple", SimpleExtractor())
    
    # Use custom extractor
    result = service.extract_from_file(
        "/path/to/document.pdf",
        method="simple"
    )
    
    print(f"Custom extractor result: {result.text}")


def example_combined_strategy():
    """Use combined extractor with different strategies"""
    print("\n=== Combined Extractor Strategies ===")
    
    service = TextExtractionService()
    pdf_path = "/path/to/document.pdf"
    
    strategies = ['best', 'first_success', 'merge']
    
    for strategy in strategies:
        print(f"\nUsing strategy: {strategy}")
        result = service.extract_from_file(
            pdf_path,
            method=ExtractionMethod.COMBINED,
            strategy=strategy,
            min_text_length=50,
            ocr_fallback=True
        )
        
        if result.success:
            print(f"Methods tried: {result.metadata.get('methods_tried')}")
            if strategy == 'best':
                print(f"Best method: {result.metadata.get('best_method')}")


def example_gemini_extraction():
    """Extract text using Gemini AI"""
    print("\n=== Gemini AI Extraction ===")
    
    # Initialize service (Gemini will be available if API key is set)
    service = TextExtractionService()
    
    pdf_path = "/path/to/complex_document.pdf"
    
    # Basic Gemini extraction
    print("\nBasic Gemini extraction:")
    result = service.extract_from_file(
        pdf_path,
        method=ExtractionMethod.GEMINI
    )
    
    if result.success:
        print(f"Extraction successful!")
        print(f"Model used: {result.metadata.get('model')}")
        print(f"Tokens used: {result.metadata.get('ai_tokens_used')}")
        print(f"First 500 characters: {result.text[:500]}")
    else:
        print(f"Failed: {result.error}")
    
    # Gemini with custom prompt
    print("\nGemini with custom prompt:")
    result = service.extract_from_file(
        pdf_path,
        method=ExtractionMethod.GEMINI,
        prompt="Extract all text and create a structured summary with main sections and key points.",
        include_formatting=True,
        extract_metadata=True
    )
    
    if result.success:
        print("Custom extraction completed!")
    
    # Combined with AI fallback
    print("\nCombined extraction with AI fallback:")
    result = service.extract_from_file(
        pdf_path,
        method=ExtractionMethod.COMBINED,
        ai_fallback=True,  # Enable AI as fallback
        ocr_fallback=True,
        min_text_length=100
    )
    
    if result.success:
        print(f"Final method used: {result.method_used}")
        print(f"All methods tried: {result.metadata.get('methods_tried')}")


def main():
    """Run all examples"""
    print("Text Extraction Service Examples")
    print("================================")
    
    # Note: Comment out examples that require actual PDF files/URLs
    # example_basic_extraction()
    # example_specific_method()
    # example_with_options()
    # example_save_to_file()
    # example_batch_extraction()
    example_custom_extractor()
    # example_combined_strategy()
    # example_gemini_extraction()
    
    print("\n\nAvailable extraction methods:")
    service = TextExtractionService()
    for method in service.get_available_methods():
        print(f"- {method}")


if __name__ == "__main__":
    main()