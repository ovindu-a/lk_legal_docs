import os
import shutil
import tempfile

import pymupdf
from utils import Log

log = Log("PDF")


class PDF:

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

    @staticmethod
    def compress(input_path, output_path):
        assert os.path.exists(input_path)
        assert input_path.endswith(".pdf")
        assert output_path.endswith(".pdf")

        temp_pdf_path = None
        if input_path == output_path:
            temp_pdf_path = tempfile.mktemp(suffix=".pdf")
            shutil.copy(input_path, temp_pdf_path)
            input_path = temp_pdf_path

        file_size_before_k = os.path.getsize(input_path) / 1000

        PDF.__compress_with_pymupdf__(input_path, output_path)

        if temp_pdf_path:
            os.remove(temp_pdf_path)

        file_size_after_k = os.path.getsize(output_path) / 1000
        p_compression = file_size_after_k / file_size_before_k
        log.debug(
            f"Compressed {input_path}"
            + f" ({file_size_before_k:,.1f}KB)"
            + f"-> {output_path}"
            + f" ({file_size_after_k:,.1f}KB, {p_compression:.1%})."
        )
