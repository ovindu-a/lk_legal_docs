from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class ExtractionMethod(Enum):
    """Available text extraction methods"""
    PYPDF2 = "pypdf2"
    PDFPLUMBER = "pdfplumber"
    PYTESSERACT = "pytesseract"
    PDFMINER = "pdfminer"
    PYMUPDF = "pymupdf"
    PYPDFIUM2 = "pypdfium2"
    PDFTOTEXT = "pdftotext"
    OCRMYPDF_PYMUPDF = "ocrmypdf_pymupdf"
    OCRMYPDF_PDFPLUMBER = "ocrmypdf_pdfplumber"
    GEMINI = "gemini"
    GEMINI_URL = "gemini_url"
    COMBINED = "combined"


@dataclass
class ExtractionResult:
    """Result of text extraction operation"""
    success: bool
    text: Optional[str] = None
    method_used: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    pages: Optional[int] = None
    extraction_time: Optional[float] = None


class BaseExtractor(ABC):
    """Abstract base class for all text extractors"""
    
    @abstractmethod
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional extractor-specific parameters
            
        Returns:
            ExtractionResult object containing the extracted text and metadata
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this extractor"""
        pass
    
    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Get list of features supported by this extractor"""
        pass
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate if the file exists and is accessible
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if file is valid and accessible
        """
        import os
        return os.path.exists(pdf_path) and os.path.isfile(pdf_path)
    
    def format_page_text(self, page_number: int, text: str) -> str:
        """
        Format text for a single page with page marker
        
        Args:
            page_number: Page number (1-indexed)
            text: Text content of the page
            
        Returns:
            Formatted text with page marker
        """
        return f"\n\n<!-- page {page_number} -->\n\n{text}"