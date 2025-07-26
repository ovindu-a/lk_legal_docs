import time
import subprocess
import tempfile
import os
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PDFToTextExtractor(BaseExtractor):
    """Text extractor using pdftotext command-line tool (from poppler-utils)"""
    
    def get_name(self) -> str:
        return "pdftotext"
    
    def get_supported_features(self) -> List[str]:
        return [
            "command_line_based",
            "fast_extraction",
            "layout_preservation",
            "raw_text_extraction",
            "physical_layout_mode",
            "table_layout_mode",
            "line_ending_preservation",
            "encoding_options"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using pdftotext command-line tool
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - layout: Maintain original physical layout (default: False)
                - raw: Keep text in raw order (default: False)
                - fixed: Assume fixed-pitch font (default: False)
                - table: Table mode for better table extraction
                - lineprinter: Use lineprinter mode
                - encoding: Output text encoding (default: UTF-8)
                - eol: End-of-line convention (unix, dos, mac)
                - nopgbrk: Don't insert page breaks
                
        Returns:
            ExtractionResult with extracted text
        """
        if not self.validate_pdf(pdf_path):
            return ExtractionResult(
                success=False,
                error=f"Invalid or missing PDF file: {pdf_path}",
                method_used=self.get_name()
            )
        
        # Check if pdftotext is available
        if not self._check_pdftotext_installed():
            return ExtractionResult(
                success=False,
                error="pdftotext not installed. Install with: apt-get install poppler-utils (Linux) or brew install poppler (Mac)",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        layout = kwargs.get('layout', False)
        raw = kwargs.get('raw', False)
        fixed = kwargs.get('fixed', False)
        table = kwargs.get('table', False)
        lineprinter = kwargs.get('lineprinter', False)
        encoding = kwargs.get('encoding', 'UTF-8')
        eol = kwargs.get('eol', 'unix')
        nopgbrk = kwargs.get('nopgbrk', False)
        
        try:
            # Build command
            cmd = ['pdftotext']
            
            # Add layout options
            if table:
                cmd.append('-table')
            elif layout:
                cmd.append('-layout')
            elif raw:
                cmd.append('-raw')
            elif fixed:
                cmd.append('-fixed')
            elif lineprinter:
                cmd.append('-lineprinter')
            
            # Add encoding
            cmd.extend(['-enc', encoding])
            
            # Add EOL option
            if eol in ['unix', 'dos', 'mac']:
                cmd.extend(['-eol', eol])
            
            # Add no page break option
            if nopgbrk:
                cmd.append('-nopgbrk')
            
            # Handle page numbers
            if page_numbers:
                # pdftotext uses first and last page options
                min_page = min(page_numbers)
                max_page = max(page_numbers)
                cmd.extend(['-f', str(min_page), '-l', str(max_page)])
            
            # Add input file and output to stdout
            cmd.extend([pdf_path, '-'])
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return ExtractionResult(
                    success=False,
                    error=f"pdftotext failed: {error_msg}",
                    method_used=self.get_name(),
                    extraction_time=time.time() - start_time
                )
            
            extracted_text = result.stdout
            
            # Get page count using pdfinfo
            total_pages = self._get_page_count(pdf_path)
            
            # Format text with page markers if not using nopgbrk
            if not nopgbrk and '\f' in extracted_text:
                # Split by form feed character (page break)
                pages = extracted_text.split('\f')
                formatted_parts = []
                for i, page_text in enumerate(pages, 1):
                    if page_text.strip():
                        formatted_parts.append(self.format_page_text(i, page_text))
                extracted_text = "".join(formatted_parts)
            
            extraction_time = time.time() - start_time
            
            metadata = {
                "total_pages": total_pages,
                "layout_mode": 'table' if table else 'layout' if layout else 'raw' if raw else 'normal',
                "encoding": encoding,
                "eol": eol,
                "page_breaks": not nopgbrk
            }
            
            if page_numbers:
                metadata["extracted_pages"] = f"{min_page}-{max_page}"
            
            return ExtractionResult(
                success=True,
                text=extracted_text,
                method_used=self.get_name(),
                pages=total_pages,
                extraction_time=extraction_time,
                metadata=metadata
            )
            
        except subprocess.TimeoutExpired:
            return ExtractionResult(
                success=False,
                error="pdftotext timed out after 5 minutes",
                method_used=self.get_name(),
                extraction_time=300
            )
        except Exception as e:
            logger.error(f"pdftotext extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def _check_pdftotext_installed(self) -> bool:
        """Check if pdftotext is installed and available"""
        try:
            result = subprocess.run(['pdftotext', '-v'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _get_page_count(self, pdf_path: str) -> int:
        """Get page count using pdfinfo"""
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        return int(line.split(':')[1].strip())
        except:
            pass
        
        return 0