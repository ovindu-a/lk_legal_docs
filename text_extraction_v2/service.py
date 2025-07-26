import os
import tempfile
import urllib.request
from typing import Dict, Optional, Union, List
import logging

from .base import ExtractionMethod, ExtractionResult, BaseExtractor
from .extractors import (
    PyPDF2Extractor,
    PDFPlumberExtractor,
    PyTesseractExtractor,
    PyMuPDFExtractor,
    PyPDFium2Extractor,
    PDFMinerExtractor,
    PDFToTextExtractor,
    OCRmyPDFExtractor,
    GeminiExtractor,
    CombinedExtractor
)

logger = logging.getLogger(__name__)


class TextExtractionService:
    """Main service for extracting text from PDFs with support for multiple methods"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize the service with all available extractors
        
        Args:
            gemini_api_key: Optional Gemini API key (uses env var if not provided)
        """
        self.extractors: Dict[str, BaseExtractor] = {
            ExtractionMethod.PYPDF2.value: PyPDF2Extractor(),
            ExtractionMethod.PDFPLUMBER.value: PDFPlumberExtractor(),
            ExtractionMethod.PYTESSERACT.value: PyTesseractExtractor(),
            ExtractionMethod.PYMUPDF.value: PyMuPDFExtractor(),
            ExtractionMethod.PYPDFIUM2.value: PyPDFium2Extractor(),
            ExtractionMethod.PDFMINER.value: PDFMinerExtractor(),
            ExtractionMethod.PDFTOTEXT.value: PDFToTextExtractor(),
            ExtractionMethod.OCRMYPDF_PYMUPDF.value: OCRmyPDFExtractor(post_ocr_extractor="pymupdf"),
            ExtractionMethod.OCRMYPDF_PDFPLUMBER.value: OCRmyPDFExtractor(post_ocr_extractor="pdfplumber"),
            ExtractionMethod.COMBINED.value: CombinedExtractor()
        }
        
        # Try to add Gemini extractor
        try:
            self.extractors[ExtractionMethod.GEMINI.value] = GeminiExtractor(api_key=gemini_api_key)
        except (ValueError, ImportError) as e:
            logger.info(f"Gemini extractor not available: {e}")
        
        # Store custom extractors separately to preserve enum values
        self.custom_extractors: Dict[str, BaseExtractor] = {}
    
    def extract_from_url(
        self,
        url: str,
        method: Union[ExtractionMethod, str] = ExtractionMethod.COMBINED,
        save_to_file: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        Extract text from a PDF URL
        
        Args:
            url: URL of the PDF to extract
            method: Extraction method to use
            save_to_file: Optional path to save extracted text
            **kwargs: Additional extractor-specific parameters
            
        Returns:
            ExtractionResult object
        """
        # Check if we should use the Gemini URL extractor for direct URL support
        method_str = method.value if isinstance(method, ExtractionMethod) else str(method)
        if method_str == ExtractionMethod.GEMINI_URL.value and ExtractionMethod.GEMINI_URL.value in self.extractors:
            # Use direct URL extraction
            extractor = self.extractors[ExtractionMethod.GEMINI_URL.value]
            result = extractor.extract_text(url, is_url=True, **kwargs)
            
            # Save to file if requested and extraction was successful
            if save_to_file and result.success and result.text:
                try:
                    with open(save_to_file, 'w', encoding='utf-8') as f:
                        f.write(result.text)
                    logger.info(f"Saved extracted text to {save_to_file}")
                    
                    if result.metadata is None:
                        result.metadata = {}
                    result.metadata['saved_to'] = save_to_file
                    
                except Exception as e:
                    logger.error(f"Failed to save text to {save_to_file}: {e}")
                    if result.metadata is None:
                        result.metadata = {}
                    result.metadata['save_error'] = str(e)
            
            return result
        
        temp_pdf_path = None
        
        try:
            # Download PDF to temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_pdf_path = temp_file.name
            
            logger.info(f"Downloading PDF from {url}")
            urllib.request.urlretrieve(url, temp_pdf_path)
            
            # Extract text from the downloaded file
            result = self.extract_from_file(temp_pdf_path, method, save_to_file, **kwargs)
            
            # Add URL to metadata
            if result.metadata is None:
                result.metadata = {}
            result.metadata['source_url'] = url
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process URL {url}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Failed to download or process URL: {str(e)}",
                method_used=str(method)
            )
        finally:
            # Clean up temporary file
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_pdf_path}: {e}")
    
    def extract_from_file(
        self,
        pdf_path: str,
        method: Union[ExtractionMethod, str] = ExtractionMethod.COMBINED,
        save_to_file: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        Extract text from a local PDF file
        
        Args:
            pdf_path: Path to the PDF file
            method: Extraction method to use
            save_to_file: Optional path to save extracted text
            **kwargs: Additional extractor-specific parameters
            
        Returns:
            ExtractionResult object
        """
        # Convert method to string if it's an enum
        if isinstance(method, ExtractionMethod):
            method_str = method.value
        else:
            method_str = str(method)
        
        # Get the appropriate extractor
        if method_str in self.extractors:
            extractor = self.extractors[method_str]
        elif method_str in self.custom_extractors:
            extractor = self.custom_extractors[method_str]
        else:
            return ExtractionResult(
                success=False,
                error=f"Unknown extraction method: {method_str}",
                method_used=method_str
            )
        
        # Extract text
        result = extractor.extract_text(pdf_path, **kwargs)
        
        # Save to file if requested and extraction was successful
        if save_to_file and result.success and result.text:
            try:
                with open(save_to_file, 'w', encoding='utf-8') as f:
                    f.write(result.text)
                logger.info(f"Saved extracted text to {save_to_file}")
                
                if result.metadata is None:
                    result.metadata = {}
                result.metadata['saved_to'] = save_to_file
                
            except Exception as e:
                logger.error(f"Failed to save text to {save_to_file}: {e}")
                # Don't fail the entire operation just because save failed
                if result.metadata is None:
                    result.metadata = {}
                result.metadata['save_error'] = str(e)
        
        return result
    
    def get_available_methods(self) -> List[str]:
        """Get list of all available extraction methods"""
        return list(self.extractors.keys()) + list(self.custom_extractors.keys())
    
    def get_method_features(self, method: Union[ExtractionMethod, str]) -> List[str]:
        """Get supported features for a specific method"""
        # Convert method to string
        if isinstance(method, ExtractionMethod):
            method_str = method.value
        else:
            method_str = str(method)
        
        if method_str in self.extractors:
            return self.extractors[method_str].get_supported_features()
        elif method_str in self.custom_extractors:
            return self.custom_extractors[method_str].get_supported_features()
        else:
            return []
    
    def register_custom_extractor(self, name: str, extractor: BaseExtractor) -> None:
        """
        Register a custom extractor
        
        Args:
            name: Name for the custom extractor
            extractor: Instance of BaseExtractor
        """
        if not isinstance(extractor, BaseExtractor):
            raise ValueError("Extractor must be an instance of BaseExtractor")
        
        self.custom_extractors[name] = extractor
        logger.info(f"Registered custom extractor: {name}")
    
    def batch_extract(
        self,
        pdf_paths: List[str],
        method: Union[ExtractionMethod, str] = ExtractionMethod.COMBINED,
        save_directory: Optional[str] = None,
        **kwargs
    ) -> Dict[str, ExtractionResult]:
        """
        Extract text from multiple PDF files
        
        Args:
            pdf_paths: List of PDF file paths
            method: Extraction method to use
            save_directory: Optional directory to save extracted text files
            **kwargs: Additional extractor-specific parameters
            
        Returns:
            Dictionary mapping file paths to ExtractionResult objects
        """
        results = {}
        
        for pdf_path in pdf_paths:
            # Determine save path if directory is provided
            save_to_file = None
            if save_directory:
                base_name = os.path.basename(pdf_path)
                name_without_ext = os.path.splitext(base_name)[0]
                save_to_file = os.path.join(save_directory, f"{name_without_ext}.txt")
            
            # Extract text
            result = self.extract_from_file(pdf_path, method, save_to_file, **kwargs)
            results[pdf_path] = result
        
        return results