import time
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PDFPlumberExtractor(BaseExtractor):
    """Text extractor using pdfplumber library - better for complex layouts"""
    
    def get_name(self) -> str:
        return "PDFPlumber"
    
    def get_supported_features(self) -> List[str]:
        return [
            "advanced_text_extraction",
            "table_extraction",
            "layout_preservation",
            "coordinate_extraction",
            "detailed_metadata"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using pdfplumber
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - extract_tables: Whether to extract tables separately
                - layout: Whether to preserve layout
                - x_tolerance: Tolerance for grouping characters horizontally
                - y_tolerance: Tolerance for grouping characters vertically
                
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
            import pdfplumber
        except ImportError:
            return ExtractionResult(
                success=False,
                error="pdfplumber not installed. Install with: pip install pdfplumber",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        extract_tables = kwargs.get('extract_tables', False)
        layout = kwargs.get('layout', False)
        x_tolerance = kwargs.get('x_tolerance', 3)
        y_tolerance = kwargs.get('y_tolerance', 3)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                if page_numbers:
                    pages_to_extract = [p - 1 for p in page_numbers if 0 < p <= total_pages]
                else:
                    pages_to_extract = range(total_pages)
                
                text_parts = []
                tables_extracted = 0
                
                for page_idx in pages_to_extract:
                    try:
                        page = pdf.pages[page_idx]
                        
                        # Extract text with specified parameters
                        extraction_params = {
                            'x_tolerance': x_tolerance,
                            'y_tolerance': y_tolerance
                        }
                        
                        if layout:
                            extraction_params['layout'] = True
                        
                        page_text = page.extract_text(**extraction_params)
                        
                        # Extract tables if requested
                        if extract_tables:
                            tables = page.extract_tables()
                            if tables:
                                tables_extracted += len(tables)
                                # Append tables as formatted text
                                for i, table in enumerate(tables):
                                    table_text = f"\n[Table {i+1}]\n"
                                    for row in table:
                                        table_text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
                                    page_text = page_text + "\n" + table_text if page_text else table_text
                        
                        if page_text:
                            formatted_text = self.format_page_text(page_idx + 1, page_text)
                            text_parts.append(formatted_text)
                        else:
                            text_parts.append(self.format_page_text(page_idx + 1, "[No text extracted]"))
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_idx + 1}: {e}")
                        text_parts.append(self.format_page_text(page_idx + 1, f"[Error: {str(e)}]"))
                
                extraction_time = time.time() - start_time
                
                metadata = {
                    "total_pages": total_pages,
                    "extracted_pages": len(pages_to_extract),
                    "layout_preserved": layout,
                    "x_tolerance": x_tolerance,
                    "y_tolerance": y_tolerance
                }
                
                if extract_tables:
                    metadata["tables_extracted"] = tables_extracted
                
                return ExtractionResult(
                    success=True,
                    text="".join(text_parts),
                    method_used=self.get_name(),
                    pages=total_pages,
                    extraction_time=extraction_time,
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )