import os
import tempfile
from functools import cache, cached_property

from utils import Log, TSVFile

from lld.www_common import WebPage

log = Log("AbstractDocDownloader")


class AbstractDocDownloader:

    DIR_TEMP_DATA = os.path.join(tempfile.gettempdir(), "lk_legal_docs_data")
    TEMP_DATA_SUMMARY_TSV_PATH = os.path.join("data", "temp_data_summary.tsv")
    TEMP_DATA_SUMMARY_TSV_PATH_DATA = os.path.join(
        DIR_TEMP_DATA, "data", "temp_data_summary.tsv"
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
            did_hot_download |= AbstractDocDownloader.__download__(
                url, file_path
            )
        return did_hot_download

    @staticmethod
    def __gen_pdf_file_paths__():
        dir_data = os.path.join(AbstractDocDownloader.DIR_TEMP_DATA, "data")
        for dir_path, _, file_names in os.walk(dir_data):
            for file_name in file_names:
                if file_name.endswith(".pdf"):
                    yield os.path.join(dir_path, file_name)

    @staticmethod
    def summarize_temp_data():
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

        n = len(d_list)
        for tsv_path in [
            AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH,
            AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH_DATA,
        ]:
            TSVFile(tsv_path).write(d_list)
            log.info(f"Wrote {n} rows to {tsv_path}")

    @staticmethod
    @cache
    def get_temp_data_summary():
        assert os.path.exists(AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH)
        return TSVFile(AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH).read()
