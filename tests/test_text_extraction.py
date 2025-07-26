import os
import tempfile
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union
from enum import Enum

import pymupdf
from pypdf import PdfReader
from utils import File, Log

log = Log("TextExtractionService")


class ExtractionMethod(Enum):
    """Available text extraction methods"""
    PYPDF = "pypdf"
    PYMUPDF = "pymupdf"
    COMBINED = "combined"  # Try multiple methods and return best result


class BaseExtractor(ABC):
    """Abstract base class for text extractors"""
    
    @abstractmethod
    def extract_text(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this extractor"""
        pass


class PyPDFExtractor(BaseExtractor):
    """Text extractor using PyPDF library"""
    
    def get_name(self) -> str:
        return "PyPDF"
    
    def extract_text(self, pdf_path: str) -> Optional[str]:
        try:
            reader = PdfReader(pdf_path)
            sections = []
            
            for i_page, page in enumerate(reader.pages, start=1):
                sections.append(f"\n\n<!-- page {i_page} -->\n\n")
                try:
                    page_text = page.extract_text()
                    sections.append(page_text or "")
                except Exception as e:
                    log.error(f"Failed to extract text from {pdf_path} - page {i_page}: {e}")
                    sections.append("")
            
            return "".join(sections)
        except Exception as e:
            log.error(f"Failed to read PDF {pdf_path} with PyPDF: {e}")
            return None


class PyMuPDFExtractor(BaseExtractor):
    """Text extractor using PyMuPDF library"""
    
    def get_name(self) -> str:
        return "PyMuPDF"
    
    def extract_text(self, pdf_path: str) -> Optional[str]:
        try:
            doc = pymupdf.open(pdf_path)
            sections = []
            
            for i_page in range(len(doc)):
                sections.append(f"\n\n<!-- page {i_page + 1} -->\n\n")
                try:
                    page = doc.load_page(i_page)
                    page_text = page.get_text()
                    sections.append(page_text or "")
                except Exception as e:
                    log.error(f"Failed to extract text from {pdf_path} - page {i_page + 1}: {e}")
                    sections.append("")
            
            doc.close()
            return "".join(sections)
        except Exception as e:
            log.error(f"Failed to read PDF {pdf_path} with PyMuPDF: {e}")
            return None


class CombinedExtractor(BaseExtractor):
    """Text extractor that tries multiple methods and returns the best result"""
    
    def __init__(self):
        self.extractors = [
            PyPDFExtractor(),
            PyMuPDFExtractor()
        ]
    
    def get_name(self) -> str:
        return "Combined"
    
    def extract_text(self, pdf_path: str) -> Optional[str]:
        best_result = None
        best_length = 0
        
        for extractor in self.extractors:
            try:
                result = extractor.extract_text(pdf_path)
                if result and len(result.strip()) > best_length:
                    best_result = result
                    best_length = len(result.strip())
                    log.debug(f"Combined extractor: {extractor.get_name()} produced {best_length} characters")
            except Exception as e:
                log.error(f"Combined extractor: {extractor.get_name()} failed: {e}")
        
        return best_result


class TextExtractionService:
    """Service for extracting text from PDFs via URL"""
    
    def __init__(self):
        self.extractors: Dict[str, BaseExtractor] = {
            ExtractionMethod.PYPDF.value: PyPDFExtractor(),
            ExtractionMethod.PYMUPDF.value: PyMuPDFExtractor(),
            ExtractionMethod.COMBINED.value: CombinedExtractor()
        }
    
    def extract_text_from_url(
        self, 
        url: str, 
        method: Union[ExtractionMethod, str] = ExtractionMethod.COMBINED,
        save_to_file: Optional[str] = None
    ) -> Dict[str, Union[str, bool, Optional[str]]]:
        """
        Extract text from a PDF URL using the specified method
        
        Args:
            url: URL of the PDF to extract text from
            method: Extraction method to use (ExtractionMethod enum or string)
            save_to_file: Optional path to save the extracted text to
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if extraction was successful
            - text: Extracted text (if successful) or None
            - method_used: Name of the method that was used
            - error: Error message (if failed) or None
        """
        # Convert method to string if it's an enum
        if isinstance(method, ExtractionMethod):
            method = method.value
        
        if method not in self.extractors:
            return {
                "success": False,
                "text": None,
                "method_used": method,
                "error": f"Unknown extraction method: {method}"
            }
        
        extractor = self.extractors[method]
        
        try:
            # Download PDF to temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_pdf_path = temp_file.name
            
            log.debug(f"Downloading PDF from {url}")
            urllib.request.urlretrieve(url, temp_pdf_path)
            
            # Extract text
            extracted_text = extractor.extract_text(temp_pdf_path)
            
            # Clean up temporary file
            os.unlink(temp_pdf_path)
            
            if extracted_text is None:
                return {
                    "success": False,
                    "text": None,
                    "method_used": extractor.get_name(),
                    "error": "Failed to extract text from PDF"
                }
            
            # Save to file if requested
            if save_to_file:
                try:
                    File(save_to_file).write(extracted_text)
                    log.debug(f"Saved extracted text to {save_to_file}")
                except Exception as e:
                    log.error(f"Failed to save text to {save_to_file}: {e}")
                    return {
                        "success": False,
                        "text": None,
                        "method_used": extractor.get_name(),
                        "error": f"Failed to save text to file: {e}"
                    }
            
            return {
                "success": True,
                "text": extracted_text,
                "method_used": extractor.get_name(),
                "error": None
            }
            
        except Exception as e:
            log.error(f"Failed to extract text from {url}: {e}")
            return {
                "success": False,
                "text": None,
                "method_used": extractor.get_name(),
                "error": str(e)
            }
    
    def get_available_methods(self) -> list[str]:
        """Get list of available extraction methods"""
        return list(self.extractors.keys())
    
    def add_custom_extractor(self, name: str, extractor: BaseExtractor):
        """Add a custom text extractor"""
        self.extractors[name] = extractor
        log.debug(f"Added custom extractor: {name}")
    
    def extract_text_from_file(
        self, 
        pdf_path: str, 
        method: Union[ExtractionMethod, str] = ExtractionMethod.COMBINED,
        save_to_file: Optional[str] = None
    ) -> Dict[str, Union[str, bool, Optional[str]]]:
        """
        Extract text from a local PDF file using the specified method
        
        Args:
            pdf_path: Path to the PDF file
            method: Extraction method to use
            save_to_file: Optional path to save the extracted text to
            
        Returns:
            Dictionary with extraction results
        """
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "text": None,
                "method_used": method,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        # Convert method to string if it's an enum
        if isinstance(method, ExtractionMethod):
            method = method.value
        
        if method not in self.extractors:
            return {
                "success": False,
                "text": None,
                "method_used": method,
                "error": f"Unknown extraction method: {method}"
            }
        
        extractor = self.extractors[method]
        
        try:
            extracted_text = extractor.extract_text(pdf_path)
            
            if extracted_text is None:
                return {
                    "success": False,
                    "text": None,
                    "method_used": extractor.get_name(),
                    "error": "Failed to extract text from PDF"
                }
            
            # Save to file if requested
            if save_to_file:
                try:
                    File(save_to_file).write(extracted_text)
                    log.debug(f"Saved extracted text to {save_to_file}")
                except Exception as e:
                    log.error(f"Failed to save text to {save_to_file}: {e}")
                    return {
                        "success": False,
                        "text": None,
                        "method_used": extractor.get_name(),
                        "error": f"Failed to save text to file: {e}"
                    }
            
            return {
                "success": True,
                "text": extracted_text,
                "method_used": extractor.get_name(),
                "error": None
            }
            
        except Exception as e:
            log.error(f"Failed to extract text from {pdf_path}: {e}")
            return {
                "success": False,
                "text": None,
                "method_used": extractor.get_name(),
                "error": str(e)
            }
```

Now let me create a simple example script to demonstrate how to use the service:

```python:examples/text_extraction_example.py
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
```

Now let me update the main `__init__.py` file to include the new service:

```python:src/lld/__init__.py
# lld (auto generate by build_inits.py)
# flake8: noqa: F408

from lld.docs import (AbstractDoc, AbstractDocBase, AbstractDocDataDownloader,
                      AbstractDocExtractText, AbstractDocPDFDownloader,
                      AbstractDocRemoteData, AbstractDocSerializer, Act, Bill,
                      DocFactory, ExtraGazette, Gazette)
from lld.reports import (ChartDocumentCountByTime, ReadMe, ReadMeDocs,
                         ReadMeSummary)
from lld.services import TextExtractionService, ExtractionMethod
from lld.www import AbstractScraper, ByYearPage, ForYearPage, GazettePages
from lld.www_common import WebPage
```

Let me also create a simple test to verify the service works:

```python:tests/test_text_extraction.py
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from lld.services.text_extraction import (
    TextExtractionService, 
    ExtractionMethod, 
    PyPDFExtractor, 
    PyMuPDFExtractor,
    CombinedExtractor,
    BaseExtractor
)


class TestTextExtractionService(unittest.TestCase):
    
    def setUp(self):
        self.service = TextExtractionService()
        self.test_pdf_path = "tests/test_data/test-compressed.pdf"
    
    def test_available_methods(self):
        """Test that all expected methods are available"""
        methods = self.service.get_available_methods()
        expected_methods = ["pypdf", "pymupdf", "combined"]
        
        for method in expected_methods:
            self.assertIn(method, methods)
    
    def test_extractors_initialized(self):
        """Test that all extractors are properly initialized"""
        self.assertIsInstance(self.service.extractors["pypdf"], PyPDFExtractor)
        self.assertIsInstance(self.service.extractors["pymupdf"], PyMuPDFExtractor)
        self.assertIsInstance(self.service.extractors["combined"], CombinedExtractor)
    
    def test_invalid_method(self):
        """Test handling of invalid extraction method"""
        result = self.service.extract_text_from_url(
            "https://example.com/test.pdf",
            method="invalid_method"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("Unknown extraction method", result["error"])
    
    def test_add_custom_extractor(self):
        """Test adding a custom extractor"""
        class CustomExtractor(BaseExtractor):
            def get_name(self):
                return "Custom"
            
            def extract_text(self, pdf_path):
                return "Custom extracted text"
        
        custom_extractor = CustomExtractor()
        self.service.add_custom_extractor("custom", custom_extractor)
        
        self.assertIn("custom", self.service.get_available_methods())
        self.assertIsInstance(self.service.extractors["custom"], CustomExtractor)
    
    def test_extract_from_file(self):
        """Test extracting text from a local file"""
        if os.path.exists(self.test_pdf_path):
            result = self.service.extract_text_from_file(
                self.test_pdf_path,
                method=ExtractionMethod.PYPDF
            )
            
            # Should succeed if the test PDF exists and is valid
            if result["success"]:
                self.assertIsNotNone(result["text"])
                self.assertEqual(result["method_used"], "PyPDF")
            else:
                # If it fails, it should be due to PDF content issues, not service issues
                self.assertIn("Failed to extract text", result["error"])
        else:
            self.skipTest(f"Test PDF file not found: {self.test_pdf_path}")
    
    def test_save_to_file(self):
        """Test saving extracted text to file"""
        if os.path.exists(self.test_pdf_path):
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                temp_txt_path = temp_file.name
            
            try:
                result = self.service.extract_text_from_file(
                    self.test_pdf_path,
                    method=ExtractionMethod.PYPDF,
                    save_to_file=temp_txt_path
                )
                
                if result["success"]:
                    self.assertTrue(os.path.exists(temp_txt_path))
                    with open(temp_txt_path, 'r', encoding='utf-8') as f:
                        saved_text = f.read()
                    self.assertEqual(saved_text, result["text"])
                else:
                    # If extraction fails, file should not be created
                    self.assertFalse(os.path.exists(temp_txt_path))
            finally:
                if os.path.exists(temp_txt_path):
                    os.unlink(temp_txt_path)
        else:
            self.skipTest(f"Test PDF file not found: {self.test_pdf_path}")


class TestExtractors(unittest.TestCase):
    
    def test_pypdf_extractor_name(self):
        """Test PyPDF extractor name"""
        extractor = PyPDFExtractor()
        self.assertEqual(extractor.get_name(), "PyPDF")
    
    def test_pymupdf_extractor_name(self):
        """Test PyMuPDF extractor name"""
        extractor = PyMuPDFExtractor()
        self.assertEqual(extractor.get_name(), "PyMuPDF")
    
    def test_combined_extractor_name(self):
        """Test Combined extractor name"""
        extractor = CombinedExtractor()
        self.assertEqual(extractor.get_name(), "Combined")
    
    def test_combined_extractor_has_sub_extractors(self):
        """Test that combined extractor has sub-extractors"""
        extractor = CombinedExtractor()
        self.assertEqual(len(extractor.extractors), 2)
        self.assertIsInstance(extractor.extractors[0], PyPDFExtractor)
        self.assertIsInstance(extractor.extractors[1], PyMuPDFExtractor)


if __name__ == '__main__':
    unittest.main()
```

Finally, let me create a comprehensive README for the text extraction service:

```markdown:docs/text_extraction_service.md
# Text Extraction Service

A flexible service for extracting text from PDF documents via URL or local file paths. The service supports multiple extraction methods and can be easily extended with custom extractors.

## Features

- **Multiple Extraction Methods**: Support for PyPDF, PyMuPDF, and combined extraction
- **URL Support**: Extract text directly from PDF URLs
- **Local File Support**: Extract text from local PDF files
- **Extensible**: Easy to add custom extraction methods
- **Error Handling**: Comprehensive error handling and logging
- **File Output**: Optional saving of extracted text to files

## Installation

The service uses existing dependencies from the project:
- `pypdf` - For PyPDF extraction method
- `pymupdf` - For PyMuPDF
```
