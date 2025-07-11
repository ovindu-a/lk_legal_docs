import os
import shutil
import tempfile

import pymupdf
from pypdf import PdfReader
from utils import File, Log

log = Log("PDF")

pymupdf.TOOLS.mupdf_display_warnings(False)
pymupdf.TOOLS.mupdf_display_errors(False)


class PDF:

    def __init__(self, pdf_path):
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        self.pdf_path = pdf_path

    def is_valid(self):
        try:
            reader = PdfReader(self.pdf_path)
            return len(reader.pages) > 0
        except Exception:
            return False

    @staticmethod
    def __compress_with_pymupdf__(input_path, output_path):
        assert input_path != output_path

        doc = pymupdf.open(input_path)
        doc.scrub(
            metadata=True,
            xml_metadata=True,
            attached_files=True,
            embedded_files=True,
            thumbnails=True,
            reset_fields=True,
            reset_responses=True,
        )
        doc.rewrite_images(
            dpi_threshold=100,
            dpi_target=72,
            quality=60,
            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True,
            set_to_gray=True,
        )
        doc.subset_fonts()
        doc.ez_save(output_path)

    def compress(self, output_path=None):
        output_path = output_path or self.pdf_path
        assert output_path.endswith(".pdf")

        input_path = self.pdf_path

        temp_pdf_path = None
        if input_path == output_path:
            temp_pdf_path = tempfile.mktemp(suffix=".pdf")
            shutil.copy(input_path, temp_pdf_path)
            input_path = temp_pdf_path

        file_size_before_k = os.path.getsize(input_path) / 1000

        try:
            PDF.__compress_with_pymupdf__(input_path, output_path)
        except Exception as e:
            log.error(f"Failed to compress {input_path}: {e}")
            shutil.copy(input_path, output_path)
            return

        file_size_after_k = os.path.getsize(output_path) / 1000
        p_compression = file_size_after_k / file_size_before_k

        log.debug(
            f"Compressed {input_path}"
            + f" ({file_size_before_k:,.1f}KB)"
            + f"-> {output_path}"
            + f" ({file_size_after_k:,.1f}KB, {p_compression:.1%})."
        )

        if p_compression > 1:
            log.warning("Compression did not reduce size. Reverting.")
            shutil.copy(input_path, output_path)
            return

    def __extract_text_for_page__(self, i_page, page, sections):
        sections.append(f"\n\n<!-- page {i_page} -->\n\n")
        page_text = None
        try:
            page_text = page.extract_text()
        except Exception as e:
            log.error(
                "Failed to extract text from"
                + f" {self.pdf_path} - page {i_page} : {e}"
            )
        sections.append(page_text or "")
        return sections

    def extract_text(self, txt_path):
        try:
            reader = PdfReader(self.pdf_path)
        except Exception as e:
            log.error(f"Failed to read PDF {self.pdf_path}: {e}")
            return False

        sections = []
        for i_page, page in enumerate(reader.pages, start=1):
            sections = self.__extract_text_for_page__(i_page, page, sections)

        content = "".join(sections)
        File(txt_path).write(content)
        file_size_k = os.path.getsize(txt_path) / 1_000
        log.debug(f"Wrote {txt_path} ({file_size_k:.0f} KB)")
        return True
