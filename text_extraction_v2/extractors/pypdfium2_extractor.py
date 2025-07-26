import time
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PyPDFium2Extractor(BaseExtractor):
    """Text extractor using pypdfium2 - Python bindings for PDFium (Chrome's PDF engine)"""
    
    def get_name(self) -> str:
        return "PyPDFium2"
    
    def get_supported_features(self) -> List[str]:
        return [
            "high_fidelity_rendering",
            "text_extraction",
            "image_rendering",
            "form_handling",
            "javascript_support",
            "chrome_compatible",
            "coordinates_extraction",
            "character_level_info"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using pypdfium2
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - get_charinfo: Whether to get character-level information
                - loose_mode: Use loose mode for better handling of special chars
                - render_mode: Rendering mode for better text extraction
                
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
            import pypdfium2 as pdfium
        except ImportError:
            return ExtractionResult(
                success=False,
                error="pypdfium2 not installed. Install with: pip install pypdfium2",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        get_charinfo = kwargs.get('get_charinfo', False)
        loose_mode = kwargs.get('loose_mode', True)
        
        try:
            # Open PDF document
            pdf = pdfium.PdfDocument(pdf_path)
            total_pages = len(pdf)
            
            if page_numbers:
                pages_to_extract = [p - 1 for p in page_numbers if 0 < p <= total_pages]
            else:
                pages_to_extract = range(total_pages)
            
            text_parts = []
            total_chars = 0
            
            for page_idx in pages_to_extract:
                try:
                    page = pdf[page_idx]
                    
                    # Get text page object
                    textpage = page.get_textpage()
                    
                    if get_charinfo:
                        # Extract with character information
                        chars_info = []
                        n_chars = textpage.count_chars()
                        
                        for i in range(n_chars):
                            char_info = textpage.get_charbox(i)
                            char = textpage.get_text_range(i, 1)
                            chars_info.append({
                                'char': char,
                                'left': char_info[0],
                                'bottom': char_info[1],
                                'right': char_info[2],
                                'top': char_info[3]
                            })
                        
                        # Reconstruct text from characters
                        page_text = ''.join(info['char'] for info in chars_info)
                        total_chars += n_chars
                    else:
                        # Simple text extraction
                        if loose_mode:
                            # Loose mode handles special characters better
                            page_text = textpage.get_text_range()
                        else:
                            # Strict mode
                            page_text = page.get_textpage().get_text_range()
                    
                    # Clean up text page object
                    textpage.close()
                    
                    if page_text:
                        formatted_text = self.format_page_text(page_idx + 1, page_text)
                        text_parts.append(formatted_text)
                    else:
                        text_parts.append(self.format_page_text(page_idx + 1, "[No text extracted]"))
                        
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_idx + 1}: {e}")
                    text_parts.append(self.format_page_text(page_idx + 1, f"[Error: {str(e)}]"))
            
            # Get document metadata
            metadata = {
                "total_pages": total_pages,
                "extracted_pages": len(pages_to_extract),
                "version": pdf.get_version() if hasattr(pdf, 'get_version') else "Unknown",
                "loose_mode": loose_mode,
                "library_version": pdfium.V if hasattr(pdfium, 'V') else "Unknown"
            }
            
            if get_charinfo:
                metadata['total_characters'] = total_chars
                metadata['character_info_extracted'] = True
            
            # Get form info if available
            try:
                formenv = pdf.init_forms()
                if formenv:
                    metadata['has_forms'] = True
                    formenv.close()
                else:
                    metadata['has_forms'] = False
            except:
                metadata['has_forms'] = False
            
            # Close the PDF
            pdf.close()
            
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                success=True,
                text="".join(text_parts),
                method_used=self.get_name(),
                pages=total_pages,
                extraction_time=extraction_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"PyPDFium2 extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )