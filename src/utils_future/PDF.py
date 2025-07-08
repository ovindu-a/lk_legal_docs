import os

import pymupdf
from utils import Log

log = Log("PDF")


class PDF:
    @staticmethod
    def compress_pdf(input_path, output_path):
        file_size_before_k = os.path.getsize(input_path) / 1000

        doc = pymupdf.open(input_path)
        doc.save(output_path, garbage=4, deflate=True)

        file_size_after_k = os.path.getsize(output_path) / 1000
        log.debug(
            f"Compressed {input_path} ({file_size_before_k:,.1f}KB)"
            + f"-> {output_path} ({file_size_after_k:,.1f}KB)."
        )
