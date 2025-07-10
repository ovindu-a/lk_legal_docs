import os
import shutil
import tempfile
from functools import cached_property

from utils import File, Log

from lld.www_common import WebPage
from utils_future import PDF, Lang

log = Log("AbstractDocDataDownloader")


class AbstractDocDataDownloader:

    DIR_TEMP_DATA = os.path.join(tempfile.gettempdir(), "lk_legal_docs_data")

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

    def get_fail_pdf_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.pdf.fail")

    @staticmethod
    def __download__(url, file_path):
        page = WebPage(url)
        try:
            page.download_binary(file_path)
            return True
        except Exception as e:
            log.error(f"Download {url} failed: {e}")
            return False

    def __download_pdf__(self, lang_code, url):
        file_path = self.get_pdf_path(lang_code)
        if os.path.exists(file_path):
            return

        if AbstractDocDataDownloader.__download__(url, file_path):
            PDF(file_path).compress()
            if PDF(file_path).is_valid():
                log.debug(f"Wrote {file_path}")
                return True

        fail_file_path = self.get_fail_pdf_path(lang_code)
        File(fail_file_path).write(self.id)
        log.debug(f"Wrote {fail_file_path}")
        return False

    def download_pdfs(self):
        did_hot_download = False
        for lang_code, url in self.lang_to_source_url.items():
            if self.__download_pdf__(lang_code, url):
                did_hot_download = True
        return did_hot_download

    def copy_metadata_to_temp_data(self):
        metadata_file_path = os.path.join(self.dir_data, "metadata.json")
        temp_metadata_file_path = os.path.join(
            self.dir_temp_data, "metadata.json"
        )
        if os.path.exists(temp_metadata_file_path):
            return False
        if not os.path.exists(self.dir_temp_data):
            os.makedirs(self.dir_temp_data, exist_ok=True)
        shutil.copyfile(metadata_file_path, temp_metadata_file_path)
        log.debug(f"Wrote {temp_metadata_file_path}")
        return True

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

    def download_all_data(self):
        is_hot = False
        is_hot |= self.copy_metadata_to_temp_data()
        is_hot |= self.download_pdfs()
        is_hot |= self.extract_text()
        return is_hot
