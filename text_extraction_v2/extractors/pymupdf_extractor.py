import time
from typing import List, Optional
import logging

from ..base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)


class PyMuPDFExtractor(BaseExtractor):
    """Text extractor using PyMuPDF (fitz) library - fast and feature-rich"""
    
    def get_name(self) -> str:
        return "PyMuPDF"
    
    def get_supported_features(self) -> List[str]:
        return [
            "fast_extraction",
            "text_blocks_extraction",
            "image_extraction",
            "metadata_extraction",
            "annotations_extraction",
            "links_extraction",
            "text_search",
            "page_rotation_handling"
        ]
    
    def extract_text(self, pdf_path: str, **kwargs) -> ExtractionResult:
        """
        Extract text using PyMuPDF (fitz)
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters:
                - page_numbers: Optional list of specific page numbers to extract
                - extract_images: Whether to extract image descriptions
                - extract_annotations: Whether to extract annotations
                - extract_links: Whether to extract hyperlinks
                - text_format: 'text', 'blocks', 'dict', 'rawdict', 'html', 'xml'
                
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
            import fitz  # PyMuPDF
        except ImportError:
            return ExtractionResult(
                success=False,
                error="PyMuPDF not installed. Install with: pip install PyMuPDF",
                method_used=self.get_name()
            )
        
        start_time = time.time()
        page_numbers = kwargs.get('page_numbers', None)
        extract_images = kwargs.get('extract_images', False)
        extract_annotations = kwargs.get('extract_annotations', False)
        extract_links = kwargs.get('extract_links', False)
        text_format = kwargs.get('text_format', 'text')
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            if page_numbers:
                pages_to_extract = [p - 1 for p in page_numbers if 0 < p <= total_pages]
            else:
                pages_to_extract = range(total_pages)
            
            text_parts = []
            annotations_count = 0
            links_count = 0
            images_count = 0
            
            for page_idx in pages_to_extract:
                try:
                    page = doc[page_idx]
                    
                    # Extract main text based on format
                    if text_format == 'blocks':
                        # Extract as text blocks with position info
                        blocks = page.get_text("blocks")
                        page_text = ""
                        for block in blocks:
                            if block[6] == 0:  # Text block (not image)
                                page_text += block[4] + "\n"
                    elif text_format == 'dict':
                        # Extract as dictionary with detailed info
                        text_dict = page.get_text("dict")
                        # Convert dict to readable text
                        page_text = self._dict_to_text(text_dict)
                    elif text_format == 'html':
                        page_text = page.get_text("html")
                    elif text_format == 'xml':
                        page_text = page.get_text("xml")
                    else:  # Default 'text'
                        page_text = page.get_text()
                    
                    # Extract annotations if requested
                    if extract_annotations:
                        annots = []
                        for annot in page.annots():
                            annots.append(f"[Annotation: {annot.info['content']}]")
                            annotations_count += 1
                        if annots:
                            page_text += "\n\n" + "\n".join(annots)
                    
                    # Extract links if requested
                    if extract_links:
                        links = page.get_links()
                        if links:
                            link_texts = []
                            for link in links:
                                if 'uri' in link:
                                    link_texts.append(f"[Link: {link['uri']}]")
                                    links_count += 1
                            if link_texts:
                                page_text += "\n\n" + "\n".join(link_texts)
                    
                    # Extract image descriptions if requested
                    if extract_images:
                        image_list = page.get_images()
                        if image_list:
                            page_text += f"\n\n[Page contains {len(image_list)} image(s)]"
                            images_count += len(image_list)
                    
                    if page_text:
                        formatted_text = self.format_page_text(page_idx + 1, page_text)
                        text_parts.append(formatted_text)
                    else:
                        text_parts.append(self.format_page_text(page_idx + 1, "[No text extracted]"))
                        
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_idx + 1}: {e}")
                    text_parts.append(self.format_page_text(page_idx + 1, f"[Error: {str(e)}]"))
            
            # Extract document metadata
            metadata = {
                "total_pages": total_pages,
                "extracted_pages": len(pages_to_extract),
                "format": doc.metadata.get('format', 'Unknown'),
                "title": doc.metadata.get('title', ''),
                "author": doc.metadata.get('author', ''),
                "subject": doc.metadata.get('subject', ''),
                "keywords": doc.metadata.get('keywords', ''),
                "creator": doc.metadata.get('creator', ''),
                "producer": doc.metadata.get('producer', ''),
                "creation_date": str(doc.metadata.get('creationDate', '')),
                "modification_date": str(doc.metadata.get('modDate', '')),
                "text_format": text_format
            }
            
            if extract_annotations:
                metadata['annotations_count'] = annotations_count
            if extract_links:
                metadata['links_count'] = links_count
            if extract_images:
                metadata['images_count'] = images_count
            
            doc.close()
            
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
            logger.error(f"PyMuPDF extraction failed for {pdf_path}: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction failed: {str(e)}",
                method_used=self.get_name(),
                extraction_time=time.time() - start_time
            )
    
    def _dict_to_text(self, text_dict: dict) -> str:
        """Convert PyMuPDF text dictionary to readable text"""
        text_parts = []
        
        for block in text_dict.get('blocks', []):
            if block.get('type') == 0:  # Text block
                for line in block.get('lines', []):
                    line_text = ""
                    for span in line.get('spans', []):
                        line_text += span.get('text', '')
                    if line_text:
                        text_parts.append(line_text)
        
        return '\n'.join(text_parts)