import time
import tempfile
import os
import subprocess
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult
from .pymupdf_extractor import PyMuPDFExtractor
from .pdfplumber_extractor import PDFPlumberExtractor

logger = logging.getLogger(__name__)


class OCRmyPDFExtractor(BaseExtractor):
    """
    OCR-based extractor that converts scanned PDFs to searchable PDFs,
    then extracts text using PyMuPDF or PDFPlumber
    """
    
    def __init__(self, post_ocr_extractor: str = "pymupdf"):
        """
        Initialize OCRmyPDF extractor
        
        Args:
            post_ocr_extractor: Which extractor to use after OCR ("pymupdf" or "pdfplumber")
        """
        self.post_ocr_extractor = post_ocr_extractor.lower()
        
        if self.post_ocr_extractor == "pymupdf":
            self.text_extractor = PyMuPDFExtractor()
        elif self.post_ocr_extractor == "pdfplumber":
            self.text_extractor = PDFPlumberExtractor()
        else:
            raise ValueError(f"Unknown post-OCR extractor: {post_ocr_extractor}")
    
    def get_name(self) -> str:
        return f"OCRmyPDF+{self.text_extractor.get_name()}"
    
    def get_supported_features(self) -> List[str]:
        return [
            "scanned_pdf_ocr",
            "searchable_pdf_creation",
            "multi_language_ocr",
            "image_preprocessing",
            "automatic_rotation",
            "background_text_layer",
            "force_ocr_option",
            "skip_text_option",
            "clean_final_pdf"
        ] + self.text_extractor.get_supported_features()
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text by first running OCR with OCRmyPDF, then extracting text
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - language: OCR language(s) (default: 'eng')
                - force_ocr: Force OCR even if text exists
                - skip_text: Skip pages that already have text
                - rotate_pages: Auto-rotate pages
                - remove_background: Remove background
                - clean: Clean pages before OCR
                - deskew: Deskew pages
                - optimize: Optimization level (0-3)
                - jpeg_quality: JPEG quality for images
                - png_quality: PNG quality for images
                Plus all parameters supported by the post-OCR extractor
                
        Returns:
            ExtractionResult with extracted text
        """
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        # Check if ocrmypdf is installed
        if not self._check_ocrmypdf_installed():
            return ExtractionResult(
                success=False,
                error="ocrmypdf not installed. Install with: pip install ocrmypdf",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        
        # OCR parameters
        language = kwargs.get('language', 'eng')
        force_ocr = kwargs.get('force_ocr', False)
        skip_text = kwargs.get('skip_text', True)
        rotate_pages = kwargs.get('rotate_pages', True)
        remove_background = kwargs.get('remove_background', False)
        clean = kwargs.get('clean', False)
        deskew = kwargs.get('deskew', False)
        optimize = kwargs.get('optimize', 1)
        jpeg_quality = kwargs.get('jpeg_quality', 0)  # 0 means default
        png_quality = kwargs.get('png_quality', 0)   # 0 means default
        
        # Create temporary file for OCR output
        temp_pdf = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                temp_pdf = tmp.name
            
            # Build OCRmyPDF command
            cmd = ['ocrmypdf']
            
            # Language option
            cmd.extend(['-l', language])
            
            # OCR options
            if force_ocr:
                cmd.append('--force-ocr')
            elif skip_text:
                cmd.append('--skip-text')
            
            if rotate_pages:
                cmd.append('--rotate-pages')
            
            if remove_background:
                cmd.append('--remove-background')
            
            if clean:
                cmd.append('--clean')
            
            if deskew:
                cmd.append('--deskew')
            
            # Optimization
            cmd.extend(['--optimize', str(optimize)])
            
            # Quality settings
            if jpeg_quality > 0:
                cmd.extend(['--jpeg-quality', str(jpeg_quality)])
            
            if png_quality > 0:
                cmd.extend(['--png-quality', str(png_quality)])
            
            # Input and output files
            cmd.extend([pdf_path, temp_pdf])
            
            # Run OCRmyPDF
            logger.info(f"Running OCRmyPDF on {pdf_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for OCR
            )
            
            ocr_time = time.time() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown OCR error"
                
                # Check if it's because the PDF already has text
                if "PriorOcrFoundError" in error_msg and not force_ocr:
                    logger.info("PDF already contains text, extracting directly")
                    # Use original PDF for extraction
                    temp_pdf = pdf_path
                else:
                    return ExtractionResult(
                        success=False,
                        error=f"OCRmyPDF failed: {error_msg}",
                        method_used=self.get_name(),
                        extraction_time=ocr_time
                    )
            
            # Extract text from OCR'd PDF using chosen extractor
            extraction_kwargs = {k: v for k, v in kwargs.items() 
                               if k not in ['language', 'force_ocr', 'skip_text', 
                                          'rotate_pages', 'remove_background', 'clean',
                                          'deskew', 'optimize', 'jpeg_quality', 'png_quality']}
            
            result = self.text_extractor.extract_text(temp_pdf, **extraction_kwargs)
            
            # Update metadata
            if result.success:
                result.method_used = self.get_name()
                result.extraction_time = time.time() - start_time
                
                if result.metadata is None:
                    result.metadata = {}
                
                result.metadata.update({
                    'ocr_performed': temp_pdf != pdf_path,
                    'ocr_language': language,
                    'ocr_time': ocr_time,
                    'post_ocr_extractor': self.text_extractor.get_name(),
                    'force_ocr': force_ocr,
                    'skip_text': skip_text,
                    'rotate_pages': rotate_pages,
                    'optimization_level': optimize
                })
            
            return result
            
        except subprocess.TimeoutExpired:
            return ExtractionResult(
                success=False,
                error="OCRmyPDF timed out after 10 minutes",
                method_used=self.get_name(),
                extraction_time=600
            )
        except Exception as e:
            logger.error(f"OCRmyPDF extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
        finally:
            # Clean up temporary file
            if temp_pdf and temp_pdf != pdf_path and os.path.exists(temp_pdf):
                try:
                    os.unlink(temp_pdf)
                except:
                    pass
    
    def _check_ocrmypdf_installed(self) -> bool:
        """Check if ocrmypdf is installed and available"""
        try:
            result = subprocess.run(['ocrmypdf', '--version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False