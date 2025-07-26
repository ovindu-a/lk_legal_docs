import time
import base64
import os
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class GeminiExtractor(BaseExtractor):
    """AI-powered text extractor using Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini extractor
        
        Args:
            api_key: Google API key. If not provided, looks for GOOGLE_API_KEY env var
            model: Gemini model to use (default: gemini-1.5-flash)
        """
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        self.model = model
        self._client = None
    
    def get_name(self) -> str:
        return f"Gemini ({self.model})"
    
    def get_supported_features(self) -> List[str]:
        return [
            "ai_powered_extraction",
            "complex_layout_understanding",
            "handwritten_text_recognition",
            "table_understanding",
            "multi_language_support",
            "image_text_extraction",
            "chart_interpretation",
            "form_field_extraction"
        ]
    
    def _get_client(self):
        """Lazy initialization of Gemini client"""
        if self._client is None:
            try:
                import google.generativeai as genai
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                )
            
            if not self.api_key:
                raise ValueError(
                    "No API key provided. Set GOOGLE_API_KEY environment variable "
                    "or pass api_key to GeminiExtractor"
                )
            
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        
        return self._client
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using Gemini AI
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - prompt: Custom prompt for extraction
                - page_numbers: Specific pages to extract (not supported - processes whole PDF)
                - include_formatting: Whether to preserve formatting hints
                - extract_metadata: Whether to extract document metadata
                
        Returns:
            ExtractionResult with extracted text
        """
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        
        try:
            # Get Gemini client
            model = self._get_client()
            
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Get optional parameters
            include_formatting = kwargs.get('include_formatting', True)
            extract_metadata = kwargs.get('extract_metadata', False)
            custom_prompt = kwargs.get('prompt', None)
            
            # Build prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._build_extraction_prompt(include_formatting, extract_metadata)
            
            # Create the request with PDF data
            response = model.generate_content([
                prompt,
                {
                    "mime_type": "application/pdf",
                    "data": pdf_base64
                }
            ])
            
            # Extract text from response
            extracted_text = response.text
            
            if not extracted_text:
                return ExtractionResult(
                    success=False,
                    error="Gemini returned empty response",
                    method_used=self.get_name(),
                    extraction_time=time.time() - start_time
                )
            
            # Post-process the extracted text
            processed_text = self._post_process_text(extracted_text, include_formatting)
            
            extraction_time = time.time() - start_time
            
            # Get file size for metadata
            file_size = os.path.getsize(pdf_path)
            
            return ExtractionResult(
                success=True,
                text=processed_text,
                method_used=self.get_name(),
                extraction_time=extraction_time,
                metadata={
                    "model": self.model,
                    "file_size_bytes": file_size,
                    "include_formatting": include_formatting,
                    "extract_metadata": extract_metadata,
                    "ai_tokens_used": getattr(response, 'usage_metadata', {}).get('total_tokens', 'unknown')
                }
            )
            
        except ImportError as e:
            return ExtractionResult(
                success=False,
                error=str(e),
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Gemini extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Gemini extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def _build_extraction_prompt(self, include_formatting: bool, extract_metadata: bool) -> str:
        """Build the extraction prompt based on options"""
        base_prompt = """Extract all text content from this PDF document. 
Please preserve the original structure and flow of the document."""
        
        if include_formatting:
            base_prompt += """
For each page, start with a page marker: <!-- page N -->
Preserve paragraph breaks and maintain the reading order."""
        
        if extract_metadata:
            base_prompt += """
Also extract and include at the beginning:
- Document title (if available)
- Author information (if available)
- Creation/modification dates (if available)
- Any other relevant metadata"""
        
        base_prompt += """
If there are tables, preserve their structure as much as possible.
If there are images with text, describe them briefly and extract any visible text.
For forms, clearly indicate field names and their values."""
        
        return base_prompt
    
    def _post_process_text(self, text: str, include_formatting: bool) -> str:
        """Post-process the extracted text"""
        # Remove any potential markdown artifacts from Gemini's response
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Skip lines that look like markdown code blocks
            if line.strip() in ['```', '```text', '```plaintext']:
                continue
            processed_lines.append(line)
        
        processed_text = '\n'.join(processed_lines)
        
        # Ensure page markers are properly formatted if not already
        if include_formatting and '<!-- page' not in processed_text:
            # Gemini might use different page markers, try to standardize them
            import re
            # Look for patterns like "Page 1", "[Page 1]", etc.
            processed_text = re.sub(
                r'(?:^|\n)\s*(?:\[)?[Pp]age\s+(\d+)(?:\])?\s*(?::|\.)?',
                r'\n\n<!-- page \1 -->\n\n',
                processed_text
            )
        
        return processed_text.strip()