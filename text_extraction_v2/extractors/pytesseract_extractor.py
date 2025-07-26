import time
from typing import List
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PyTesseractExtractor(BaseExtractor):
    """OCR-based text extractor using pytesseract - for scanned PDFs"""
    
    def get_name(self) -> str:
        return "PyTesseract"
    
    def get_supported_features(self) -> List[str]:
        return [
            "ocr_extraction",
            "scanned_pdf_support",
            "multi_language_support",
            "image_preprocessing",
            "handwritten_text_support"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using OCR with pytesseract
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - language: OCR language (default: 'eng')
                - dpi: DPI for PDF to image conversion (default: 300)
                - preprocess: Whether to preprocess images (default: True)
                - psm: Page segmentation mode (default: 3)
                
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
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            from PIL import ImageEnhance
            from PIL import ImageFilter
        except ImportError as e:
            missing_lib = str(e).split("'")[1]
            install_cmd = {
                'pytesseract': 'pip install pytesseract',
                'pdf2image': 'pip install pdf2image',
                'PIL': 'pip install Pillow'
            }.get(missing_lib, f'pip install {missing_lib}')
            
            return ExtractionResult(
                success=False,
                error=f"{missing_lib} not installed. Install with: {install_cmd}. Also ensure Tesseract OCR is installed on your system.",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        language = kwargs.get('language', 'eng')
        dpi = kwargs.get('dpi', 300)
        preprocess = kwargs.get('preprocess', True)
        psm = kwargs.get('psm', 3)  # Page segmentation mode
        
        try:
            # Convert PDF to images
            if page_numbers:
                images = []
                for page_num in page_numbers:
                    try:
                        page_images = convert_from_path(
                            pdf_path, 
                            dpi=dpi, 
                            first_page=page_num, 
                            last_page=page_num
                        )
                        images.extend(page_images)
                    except Exception as e:
                        logger.warning(f"Failed to convert page {page_num}: {e}")
            else:
                images = convert_from_path(pdf_path, dpi=dpi)
            
            total_pages = len(images)
            text_parts = []
            
            # Configure pytesseract
            custom_config = f'--psm {psm}'
            
            for i, image in enumerate(images):
                try:
                    # Preprocess image if requested
                    if preprocess:
                        image = self._preprocess_image(image)
                    
                    # Extract text using OCR
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang=language,
                        config=custom_config
                    )
                    
                    if page_text.strip():
                        formatted_text = self.format_page_text(i + 1, page_text)
                        text_parts.append(formatted_text)
                    else:
                        text_parts.append(self.format_page_text(i + 1, "[No text detected]"))
                        
                except Exception as e:
                    logger.warning(f"OCR failed for page {i + 1}: {e}")
                    text_parts.append(self.format_page_text(i + 1, f"[OCR Error: {str(e)}]"))
            
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                success=True,
                text="".join(text_parts),
                method_used=self.get_name(),
                pages=total_pages,
                extraction_time=extraction_time,
                metadata={
                    "total_pages": total_pages,
                    "language": language,
                    "dpi": dpi,
                    "preprocessing": preprocess,
                    "psm": psm,
                    "tesseract_version": pytesseract.get_tesseract_version().decode('utf-8')
                }
            )
            
        except Exception as e:
            logger.error(f"PyTesseract extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"OCR extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def _preprocess_image(self, image):
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        return image