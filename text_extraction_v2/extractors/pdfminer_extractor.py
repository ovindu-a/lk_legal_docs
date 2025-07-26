import time
from typing import List, Optional
import logging
from io import StringIO

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PDFMinerExtractor(BaseExtractor):
    """Text extractor using pdfminer.six - detailed layout analysis"""
    
    def get_name(self) -> str:
        return "PDFMiner.six"
    
    def get_supported_features(self) -> List[str]:
        return [
            "detailed_layout_analysis",
            "text_position_extraction",
            "font_information",
            "color_information",
            "advanced_cjk_support",
            "text_box_detection",
            "line_detection",
            "paragraph_detection"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using pdfminer.six
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - laparams: LAParams for layout analysis
                - password: PDF password if encrypted
                - maxpages: Maximum pages to process
                - caching: Enable caching (default: True)
                - codec: Text codec (default: utf-8)
                - detect_vertical: Detect vertical text (for CJK)
                
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
            from pdfminer.high_level import extract_text_to_fp, extract_pages
            from pdfminer.layout import LAParams, LTTextBox, LTChar, LTFigure, LTTextLine
            from pdfminer.pdfpage import PDFPage
        except ImportError:
            return ExtractionResult(
                success=False,
                error="pdfminer.six not installed. Install with: pip install pdfminer.six",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        password = kwargs.get('password', '')
        maxpages = kwargs.get('maxpages', 0)
        caching = kwargs.get('caching', True)
        codec = kwargs.get('codec', 'utf-8')
        detect_vertical = kwargs.get('detect_vertical', False)
        
        # Get or create LAParams
        laparams = kwargs.get('laparams', None)
        if laparams is None:
            laparams = LAParams(
                detect_vertical=detect_vertical,
                char_margin=2.0,
                line_margin=0.5,
                word_margin=0.1,
                boxes_flow=0.5
            )
        
        try:
            # First, get total page count
            with open(pdf_path, 'rb') as fp:
                total_pages = len(list(PDFPage.get_pages(
                    fp, pagenos=None, maxpages=0, password=password, caching=caching
                )))
            
            # Determine pages to extract
            if page_numbers:
                pages_to_extract = [p - 1 for p in page_numbers if 0 < p <= total_pages]
            else:
                pages_to_extract = None  # Extract all
            
            # Extract text with layout analysis
            output_string = StringIO()
            with open(pdf_path, 'rb') as fp:
                extract_text_to_fp(
                    fp,
                    output_string,
                    laparams=laparams,
                    output_type='text',
                    codec=codec,
                    page_numbers=pages_to_extract,
                    maxpages=maxpages,
                    password=password,
                    caching=caching
                )
            
            extracted_text = output_string.getvalue()
            
            # If requested, also get detailed layout information
            if kwargs.get('detailed_layout', False):
                layout_info = self._extract_detailed_layout(
                    pdf_path, password, pages_to_extract, laparams, caching
                )
            else:
                layout_info = None
            
            extraction_time = time.time() - start_time
            
            metadata = {
                "total_pages": total_pages,
                "extracted_pages": len(pages_to_extract) if pages_to_extract else total_pages,
                "codec": codec,
                "detect_vertical": detect_vertical,
                "caching": caching,
                "layout_analysis": True
            }
            
            if layout_info:
                metadata['layout_info'] = layout_info
            
            return ExtractionResult(
                success=True,
                text=extracted_text,
                method_used=self.get_name(),
                pages=total_pages,
                extraction_time=extraction_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"PDFMiner extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def _extract_detailed_layout(self, pdf_path: str, password: str, 
                                page_numbers: Optional[List[int]], 
                                laparams: 'LAParams', caching: bool) -> dict:
        """Extract detailed layout information from PDF"""
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextBox, LTChar, LTFigure, LTTextLine
        
        layout_info = {
            'text_boxes': 0,
            'text_lines': 0,
            'characters': 0,
            'figures': 0,
            'fonts_used': set()
        }
        
        try:
            for page_num, page_layout in enumerate(extract_pages(
                pdf_path, password=password, page_numbers=page_numbers,
                laparams=laparams, caching=caching
            )):
                for element in page_layout:
                    if isinstance(element, LTTextBox):
                        layout_info['text_boxes'] += 1
                        for line in element:
                            if isinstance(line, LTTextLine):
                                layout_info['text_lines'] += 1
                                for char in line:
                                    if isinstance(char, LTChar):
                                        layout_info['characters'] += 1
                                        if hasattr(char, 'fontname'):
                                            layout_info['fonts_used'].add(char.fontname)
                    elif isinstance(element, LTFigure):
                        layout_info['figures'] += 1
            
            # Convert set to list for JSON serialization
            layout_info['fonts_used'] = list(layout_info['fonts_used'])
            
        except Exception as e:
            logger.warning(f"Failed to extract detailed layout: {e}")
        
        return layout_info