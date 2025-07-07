import os
import tempfile
from functools import cache, cached_property

from utils import Log, TSVFile

from lld.www_common import WebPage
from utils_future import Lang

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
        return os.path.join(
            AbstractDocDownloader.DIR_TEMP_DATA, self.dir_data
        )

    def get_pdf_path(self, lang):
        return os.path.join(self.dir_temp_data, f"{lang}.pdf")

    def download_all(self):
        did_hot_download = False
        for lang, url in self.lang_to_source_url.items():
            if not url:
                continue
            file_path = self.get_pdf_path(lang)
            if not os.path.exists(file_path):
                page = WebPage(url)
                os.makedirs(self.dir_temp_data, exist_ok=True)
                page.download_binary(file_path)
                did_hot_download = True

        return did_hot_download

    @staticmethod
    def summarize_temp_data():
        dir_data = os.path.join(AbstractDocDownloader.DIR_TEMP_DATA, "data")
        d_list = []
        for doc_type_name in os.listdir(dir_data):
            dir_data_doc_type = os.path.join(dir_data, doc_type_name)
            if not os.path.isdir(dir_data_doc_type):
                continue
            for year in os.listdir(dir_data_doc_type):
                dir_data_year = os.path.join(dir_data_doc_type, year)
                if not os.path.isdir(dir_data_year):
                    continue
                for doc_id in os.listdir(dir_data_year):
                    dir_data_doc = os.path.join(dir_data_year, doc_id)
                    if not os.path.isdir(dir_data_doc):
                        continue

                    has_pdf_idx = {}
                    for lang in Lang.list_all():
                        pdf_path = os.path.join(
                            dir_data_doc, f"{lang.code}.pdf"
                        )
                        has_pdf_idx[lang.code] = os.path.exists(pdf_path)

                    d = dict(
                        doc_type_name=doc_type_name,
                        doc_id=doc_id,
                        year=year,
                        has_si=has_pdf_idx["si"],
                        has_en=has_pdf_idx["en"],
                        has_ta=has_pdf_idx["ta"],
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
        assert os.path.exists(
            AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH
        )
        return TSVFile(
            AbstractDocDownloader.TEMP_DATA_SUMMARY_TSV_PATH
        ).read()
