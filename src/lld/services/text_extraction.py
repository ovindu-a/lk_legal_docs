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