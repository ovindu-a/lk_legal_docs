import time
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PyPDF2Extractor(BaseExtractor):
    """Text extractor using PyPDF2 library"""
    
    def get_name(self) -> str:
        return "PyPDF2"
    
    def get_supported_features(self) -> List[str]:
        return [
            "basic_text_extraction",
            "page_by_page_extraction",
            "fast_processing",
            "low_memory_usage"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using PyPDF2
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - layout_mode: Whether to preserve layout (not supported by PyPDF2)
                
        Returns:
            ExtractionResult with extracted text
        """
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        try:
            import PyPDF2
        except ImportError:
            return ExtractionResult(
                success=False,
                error="PyPDF2 not installed. Install with: pip install PyPDF2",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                if page_numbers:
                    pages_to_extract = [p - 1 for p in page_numbers if 0 < p <= total_pages]
                else:
                    pages_to_extract = range(total_pages)
                
                text_parts = []
                
                for page_idx in pages_to_extract:
                    try:
                        page = reader.pages[page_idx]
                        page_text = page.extract_text()
                        
                        if page_text:
                            formatted_text = self.format_page_text(page_idx + 1, page_text)
                            text_parts.append(formatted_text)
                        else:
                            text_parts.append(self.format_page_text(page_idx + 1, "[No text extracted]"))
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_idx + 1}: {e}")
                        text_parts.append(self.format_page_text(page_idx + 1, f"[Error: {str(e)}]"))
                
                extraction_time = time.time() - start_time
                
                return ExtractionResult(
                    success=True,
                    text="".join(text_parts),
                    method_used=self.get_name(),
                    pages=total_pages,
                    extraction_time=extraction_time,
                    metadata={
                        "total_pages": total_pages,
                        "extracted_pages": len(pages_to_extract),
                        "library_version": PyPDF2.__version__ if hasattr(PyPDF2, '__version__') else "unknown"
                    }
                )
                
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )