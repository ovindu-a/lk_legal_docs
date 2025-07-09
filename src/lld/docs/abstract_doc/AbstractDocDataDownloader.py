import os
import shutil
import tempfile
from functools import cached_property

from utils import Log

from lld.www_common import WebPage
from utils_future import PDF, Lang

log = Log("AbstractDocDataDownloader")


class AbstractDocDataDownloader:

    DIR_TEMP_DATA = os.path.join(tempfile.gettempdir(), "lk_legal_docs_data")

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
        return os.path.join(
            AbstractDocDataDownloader.DIR_TEMP_DATA, self.dir_data
        )

    def get_pdf_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.pdf")

    @staticmethod
    def __download__(url, file_path):
        page = WebPage(url)
        try:
            page.download_binary(file_path)
            return True
        except Exception as e:
            log.error(f"Download {url} failed: {e}")
            return False

    def download_all_pdfs(self):
        did_hot_download = False
        for lang, url in self.lang_to_source_url.items():
            if not url:
                continue
            file_path = self.get_pdf_path(lang)
            if os.path.exists(file_path):
                continue
            os.makedirs(self.dir_temp_data, exist_ok=True)
            if AbstractDocDataDownloader.__download__(url, file_path):
                did_hot_download = True
                PDF(file_path).compress()
        return did_hot_download

    def copy_metadata_to_temp_data(self):
        metadata_file_path = os.path.join(self.dir_data, "metadata.json")
        temp_metadata_file_path = os.path.join(
            self.dir_temp_data, "metadata.json"
        )
        if os.path.exists(temp_metadata_file_path):
            return
        if not os.path.exists(self.dir_temp_data):
            os.makedirs(self.dir_temp_data, exist_ok=True)
        shutil.copyfile(metadata_file_path, temp_metadata_file_path)
        log.debug(f"Wrote {temp_metadata_file_path}")

    @cached_property
    def n_pdfs(self):
        n_pdfs = 0
        for lang in Lang.list_all():
            pdf_path = self.get_pdf_path(lang.code)
            if os.path.exists(pdf_path):
                n_pdfs += 1
        return n_pdfs

    @cached_property
    def remote_data_url(self):
        return (
            "https://github.com/nuuuwan/lk_legal_docs_data/tree/main/data"
            + f"/{self.get_doc_type_name()}/{self.year}/{self.id}"
        )

    def get_remote_pdf_path(self, lang_code):
        return f"{self.remote_data_url}/{lang_code}.pdf"

    def get_remote_txt_path(self, lang_code):
        return f"{self.remote_data_url}/{lang_code}.txt"

    def get_remote_metadata_path(self):
        return f"{self.remote_data_url}/metadata.json"
