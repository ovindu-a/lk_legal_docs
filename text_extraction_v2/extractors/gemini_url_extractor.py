import time
import os
from typing import List, Optional, Union
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv() 


class GeminiURLExtractor(BaseExtractor):
    """AI-powered text extractor using Google's Gemini API with direct URL support"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini URL extractor
        
        Args:
            api_key: Google API key. If not provided, looks for GOOGLE_API_KEY env var
            model: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        self.model = model
        self._client = None
    
    def get_name(self) -> str:
        return f"Gemini URL ({self.model})"
    
    def get_supported_features(self) -> List[str]:
        return [
            "ai_powered_extraction",
            "complex_layout_understanding",
            "handwritten_text_recognition",
            "table_understanding",
            "multi_language_support",
            "image_text_extraction",
            "chart_interpretation",
            "form_field_extraction",
            "direct_url_support",
            "no_temp_file_needed"
        ]
    
    def _get_client(self):
        """Lazy initialization of Gemini client"""
        if self._client is None:
            try:
                from google import genai
            except ImportError:
                raise ImportError(
                    "google-genai not installed. "
                    "Install with: pip install google-genai"
                )
            
            if not self.api_key:
                raise ValueError(
                    "No API key provided. Set GOOGLE_API_KEY environment variable "
                    "or pass api_key to GeminiURLExtractor"
                )
            
            self._client = genai.Client(api_key=self.api_key)
        
        return self._client
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using Gemini AI from a file path or URL
        
        Args:
            pdf_path: Path to the PDF file or URL
            **kwargs: Additional parameters:
                - prompt: Custom prompt for extraction
                - include_formatting: Whether to preserve formatting hints
                - extract_metadata: Whether to extract document metadata
                - is_url: Whether pdf_path is a URL (auto-detected if not specified)
                
        Returns:
            ExtractionResult with extracted text
        """
        # Auto-detect if it's a URL
        is_url = kwargs.get('is_url', pdf_path.startswith(('http://', 'https://')))
        
        if not is_url and not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        
        try:
            # Import required libraries
            try:
                from google.genai import types
                import httpx
            except ImportError as e:
                return ExtractionResult(
                    success=False,
                    error=f"Missing required dependency: {str(e)}. Install with: pip install google-genai httpx",
                    method_used=self.get_name(),
                    extraction_time=time.time() - start_time
                )
            
            # Get Gemini client
            client = self._get_client()
            
            # Get PDF data
            if is_url:
                # Download from URL
                try:
                    doc_data = httpx.get(pdf_path).content
                    source_info = {"source_url": pdf_path}
                except Exception as e:
                    return ExtractionResult(
                        success=False,
                        error=f"Failed to download PDF from URL: {str(e)}",
                        method_used=self.get_name(),
                        extraction_time=time.time() - start_time
                    )
            else:
                # Read from file
                with open(pdf_path, 'rb') as f:
                    doc_data = f.read()
                source_info = {"source_file": pdf_path}
            
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
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(
                        data=doc_data,
                        mime_type='application/pdf',
                    ),
                    prompt
                ]
            )
            
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
            
            # Build metadata
            metadata = {
                "model": self.model,
                "file_size_bytes": len(doc_data),
                "include_formatting": include_formatting,
                "extract_metadata": extract_metadata,
                "is_url": is_url,
                **source_info
            }
            
            # Add token usage if available
            if hasattr(response, 'usage_metadata'):
                metadata["ai_tokens_used"] = getattr(response.usage_metadata, 'total_tokens', 'unknown')
            
            return ExtractionResult(
                success=True,
                text=processed_text,
                method_used=self.get_name(),
                extraction_time=extraction_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Gemini URL extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Gemini URL extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def extract_from_url(self, url: str, **kwargs) -> ExtractionResult:
        """
        Convenience method for extracting from URLs
        
        Args:
            url: URL of the PDF document
            **kwargs: Additional parameters passed to extract_text
            
        Returns:
            ExtractionResult with extracted text
        """
        kwargs['is_url'] = True
        return self.extract_text(url, **kwargs)
    
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