import os
import subprocess

from utils import Log

log = Log("PDF")


class PDF:
    @staticmethod
    def compress_pdf(input_path, output_path, quality="ebook"):
        file_size_before_k = os.path.getsize(input_path) / 1000
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]
        subprocess.run(gs_command, check=True)
        file_size_after_k = os.path.getsize(output_path) / 1000
        log.debug(
            f"Compressed {input_path} ({file_size_before_k:,.1f}KB)"
            + f"-> {output_path} ({file_size_after_k:,.1f}KB)."
        )
