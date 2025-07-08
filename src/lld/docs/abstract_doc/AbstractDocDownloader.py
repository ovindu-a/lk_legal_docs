import os
import subprocess
import tempfile
from functools import cache, cached_property

from utils import JSONFile, Log, TSVFile

from lld.www_common import WebPage
from utils_future import Directory

log = Log("AbstractDocDownloader")


class AbstractDocDownloader:

    DIR_TEMP_DATA = os.path.join(tempfile.gettempdir(), "lk_legal_docs_data")
    DATA_SUMMARY_TSV_PATH = os.path.join("data", "temp_data_summary.tsv")
    TEMP_DATA_SUMMARY_TSV_PATH = os.path.join(
        DIR_TEMP_DATA, "data", "temp_data_summary.tsv"
    )

    DATA_SUMMARY_JSON_PATH = os.path.join("data", "temp_data_summary.json")
    TEMP_DATA_SUMMARY_JSON_PATH = os.path.join(
        DIR_TEMP_DATA, "data", "temp_data_summary.json"
    )

    @cached_property
    def dir_data(self):
        dir_data = os.path.join(self.get_doc_type_dir(), self.year, self.id)
        return dir_data

    @cached_property
    def dir_temp_data(self):
        return os.path.join(AbstractDocDownloader.DIR_TEMP_DATA, self.dir_data)

    def get_pdf_path(self, lang):
        return os.path.join(self.dir_temp_data, f"{lang}.pdf")

    @staticmethod
    def __download__(url, file_path):
        page = WebPage(url)
        try:
            page.download_binary(file_path)
            return True
        except Exception as e:
            log.error(f"Download {url} failed: {e}")
            return False

    def download_all(self):
        did_hot_download = False
        for lang, url in self.lang_to_source_url.items():
            if not url:
                continue
            file_path = self.get_pdf_path(lang)
            if os.path.exists(file_path):
                continue
            os.makedirs(self.dir_temp_data, exist_ok=True)
            if AbstractDocDownloader.__download__(url, file_path):
                did_hot_download = True
                AbstractDocDownloader.compress_pdf(file_path, file_path)
        return did_hot_download

    @staticmethod
    def __gen_pdf_file_paths__():
        dir_data = os.path.join(AbstractDocDownloader.DIR_TEMP_DATA, "data")
        for dir_path, _, file_names in os.walk(dir_data):
            for file_name in file_names:
                if file_name.endswith(".pdf"):
                    yield os.path.join(dir_path, file_name)

    @staticmethod
    def __get_temp_data_d_list__():
        d_list = []
        for pdf_file_path in AbstractDocDownloader.__gen_pdf_file_paths__():
            path_parts = pdf_file_path.split(os.sep)

            doc_type_name, year, doc_id, file_name = path_parts[-4:]
            lang_code = file_name[:2]
            d = dict(
                doc_type_name=doc_type_name,
                doc_id=doc_id,
                year=year,
                lang_code=lang_code,
            )
            d_list.append(d)
        return d_list

    @staticmethod
    def build_tsv(d_list):

        n = len(d_list)
        for tsv_path in [
            AbstractDocDownloader.DATA_SUMMARY_TSV_PATH,
            AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH,
        ]:
            TSVFile(tsv_path).write(d_list)
            log.info(f"Wrote {n} rows to {tsv_path}")

    @staticmethod
    def build_json(d_list):
        d = dict(
            n_pdfs=len(d_list),
            n_unique_docs=len(set((d["doc_id"]) for d in d_list)),
            total_file_size=Directory(
                AbstractDocDownloader.DIR_TEMP_DATA
            ).size,
        )

        for json_path in [
            AbstractDocDownloader.DATA_SUMMARY_JSON_PATH,
            AbstractDocDownloader.TEMP_DATA_SUMMARY_JSON_PATH,
        ]:
            JSONFile(json_path).write(d)
            log.info(f"Wrote {json_path}")

    @staticmethod
    def summarize_temp_data():
        d_list = AbstractDocDownloader.__get_temp_data_d_list__()
        AbstractDocDownloader.build_tsv(d_list)
        AbstractDocDownloader.build_json(d_list)

    @staticmethod
    @cache
    def get_temp_data_summary():
        assert os.path.exists(AbstractDocDownloader.DATA_SUMMARY_JSON_PATH)
        return JSONFile(AbstractDocDownloader.DATA_SUMMARY_JSON_PATH).read()

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
