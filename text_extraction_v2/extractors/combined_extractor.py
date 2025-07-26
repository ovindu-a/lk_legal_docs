import time
from typing import List, Optional, Dict, Any
import logging

from ..base import BaseExtractor, ExtractionResult
from .pypdf2_extractor import PyPDF2Extractor
from .pdfplumber_extractor import PDFPlumberExtractor
from .pytesseract_extractor import PyTesseractExtractor
from .gemini_extractor import GeminiExtractor

logger = logging.getLogger(__name__)


class CombinedExtractor(BaseExtractor):
    """Combined extractor that tries multiple methods and returns the best result"""
    
    def __init__(self, extractors: Optional[List[BaseExtractor]] = None):
        """
        Initialize with specific extractors or use defaults
        
        Args:
            extractors: List of extractors to use. If None, uses defaults (non-AI extractors).
        """
        if extractors:
            self.extractors = extractors
        else:
            # Default to non-AI extractors for Combined mode
            # Users can explicitly use Gemini by selecting it as the method
            self.extractors = [
                PyPDF2Extractor(),
                PDFPlumberExtractor(),
                PyTesseractExtractor()
            ]
    
    def get_name(self) -> str:
        return "Combined"
    
    def get_supported_features(self) -> List[str]:
        """Combines features from all extractors"""
        features = set()
        for extractor in self.extractors:
            features.update(extractor.get_supported_features())
        return list(features)
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Try multiple extraction methods and return the best result
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - strategy: 'best' (default), 'first_success', 'merge'
                - min_text_length: Minimum text length to consider valid
                - ocr_fallback: Whether to use OCR if text extraction fails
                
        Returns:
            ExtractionResult with the best extracted text
        """
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        strategy = kwargs.get('strategy', 'best')
        min_text_length = kwargs.get('min_text_length', 100)
        ocr_fallback = kwargs.get('ocr_fallback', True)
        
        results = []
        methods_tried = []
        
        # Categorize extractors
        basic_extractors = [e for e in self.extractors 
                           if not isinstance(e, (PyTesseractExtractor, GeminiExtractor))]
        ocr_extractors = [e for e in self.extractors if isinstance(e, PyTesseractExtractor)]
        ai_extractors = [e for e in self.extractors if isinstance(e, GeminiExtractor)]
        
        # Try basic methods first (fastest and cheapest)
        for extractor in basic_extractors:
            try:
                result = extractor.extract_text(pdf_path, **kwargs)
                results.append(result)
                methods_tried.append(extractor.get_name())
                
                # For 'first_success' strategy, return immediately if successful
                if strategy == 'first_success' and result.success and result.text and len(result.text.strip()) >= min_text_length:
                    result.metadata = result.metadata or {}
                    result.metadata['methods_tried'] = methods_tried
                    result.method_used = f"Combined ({result.method_used})"
                    return result
                    
            except Exception as e:
                logger.warning(f"Extractor {extractor.get_name()} failed: {e}")
        
        # Check if we need fallback methods
        need_fallback = all(
            not r.success or not r.text or len(r.text.strip()) < min_text_length 
            for r in results
        )
        
        # Try OCR if needed and enabled
        if need_fallback and ocr_fallback and ocr_extractors:
            for extractor in ocr_extractors:
                try:
                    result = extractor.extract_text(pdf_path, **kwargs)
                    results.append(result)
                    methods_tried.append(extractor.get_name())
                    
                    if strategy == 'first_success' and result.success and result.text:
                        result.metadata = result.metadata or {}
                        result.metadata['methods_tried'] = methods_tried
                        result.method_used = f"Combined ({result.method_used})"
                        return result
                        
                except Exception as e:
                    logger.warning(f"OCR extractor {extractor.get_name()} failed: {e}")
        
        # Try AI extractors as last resort (most expensive)
        use_ai_fallback = kwargs.get('ai_fallback', False)
        if need_fallback and use_ai_fallback and ai_extractors:
            for extractor in ai_extractors:
                try:
                    result = extractor.extract_text(pdf_path, **kwargs)
                    results.append(result)
                    methods_tried.append(extractor.get_name())
                    
                    if strategy == 'first_success' and result.success and result.text:
                        result.metadata = result.metadata or {}
                        result.metadata['methods_tried'] = methods_tried
                        result.method_used = f"Combined ({result.method_used})"
                        return result
                        
                except Exception as e:
                    logger.warning(f"AI extractor {extractor.get_name()} failed: {e}")
        
        # Process results based on strategy
        if strategy == 'merge':
            return self._merge_results(results, methods_tried, time.time() - start_time)
        else:  # 'best' strategy
            return self._select_best_result(results, methods_tried, time.time() - start_time, min_text_length)
    
    def _select_best_result(self, results: List[ExtractionResult], methods_tried: List[str], 
                           total_time: float, min_text_length: int) -> ExtractionResult:
        """Select the best result based on success and text length"""
        
        # Filter successful results
        successful_results = [r for r in results if r.success and r.text]
        
        if not successful_results:
            # No successful extraction
            errors = [r.error for r in results if r.error]
            return ExtractionResult(
                success=False,
                error=f"All extraction methods failed. Errors: {'; '.join(errors)}",
                method_used=self.get_name(),
                extraction_time=total_time,
                metadata={'methods_tried': methods_tried}
            )
        
        # Sort by text length (descending)
        successful_results.sort(key=lambda r: len(r.text.strip()), reverse=True)
        best_result = successful_results[0]
        
        # Create combined result
        return ExtractionResult(
            success=True,
            text=best_result.text,
            method_used=f"Combined ({best_result.method_used})",
            pages=best_result.pages,
            extraction_time=total_time,
            metadata={
                'methods_tried': methods_tried,
                'best_method': best_result.method_used,
                'text_lengths': {r.method_used: len(r.text.strip()) for r in successful_results},
                'original_metadata': best_result.metadata
            }
        )
    
    def _merge_results(self, results: List[ExtractionResult], methods_tried: List[str], 
                      total_time: float) -> ExtractionResult:
        """Merge results from multiple extractors"""
        
        # For merge strategy, we'll combine unique content from each extractor
        # This is a simple implementation - could be made more sophisticated
        
        successful_results = [r for r in results if r.success and r.text]
        
        if not successful_results:
            errors = [r.error for r in results if r.error]
            return ExtractionResult(
                success=False,
                error=f"All extraction methods failed. Errors: {'; '.join(errors)}",
                method_used=self.get_name(),
                extraction_time=total_time,
                metadata={'methods_tried': methods_tried}
            )
        
        # For simplicity, just use the longest text
        # In a more sophisticated implementation, you could merge content intelligently
        merged_text = max(successful_results, key=lambda r: len(r.text.strip())).text
        
        return ExtractionResult(
            success=True,
            text=merged_text,
            method_used=f"Combined (Merged)",
            extraction_time=total_time,
            metadata={
                'methods_tried': methods_tried,
                'merge_strategy': 'longest_text',
                'source_results': len(successful_results)
            }
        )