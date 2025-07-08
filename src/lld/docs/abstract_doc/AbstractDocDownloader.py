import os
import shutil
import tempfile
from functools import cache, cached_property

from utils import JSONFile, Log

from lld.www_common import WebPage
from utils_future import PDF, Directory, Lang

log = Log("AbstractDocDownloader")


class AbstractDocDownloader:

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
                PDF.compress(file_path, file_path)
        return did_hot_download

    @staticmethod
    def __gen_doc_type_dir_paths__():
        dir_data = os.path.join(AbstractDocDownloader.DIR_TEMP_DATA, "data")
        for doc_type_name in os.listdir(dir_data):
            doc_type_dir = os.path.join(dir_data, doc_type_name)
            if not os.path.isdir(doc_type_dir):
                continue
            yield doc_type_dir

    @staticmethod
    def __gen_year_dirs__():
        for doc_type_dir in AbstractDocDownloader.__gen_doc_type_dir_paths__():
            for year in os.listdir(doc_type_dir):
                year_dir = os.path.join(doc_type_dir, year)
                if not os.path.isdir(year_dir):
                    continue
                yield year_dir

    @staticmethod
    def __gen_dir_data_paths__():
        for year_dir in AbstractDocDownloader.__gen_year_dirs__():
            for doc_id in os.listdir(year_dir):
                dir_data = os.path.join(year_dir, doc_id)
                if not os.path.isdir(dir_data):
                    continue
                yield dir_data

    @staticmethod
    def __get_temp_data_d_list__():
        d_list = []
        for dir_data in AbstractDocDownloader.__gen_dir_data_paths__():
            metadata_file_path = os.path.join(dir_data, "metadata.json")
            d = JSONFile(metadata_file_path).read()

            n_pdfs = 0
            for lang in Lang.list_all():
                pdf_file_path = os.path.join(dir_data, f"{lang.code}.pdf")
                if os.path.exists(pdf_file_path):
                    n_pdfs += 1
            d["n_pdfs"] = n_pdfs

            d_list.append(d)
        return d_list

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

    @staticmethod
    def build_json(d_list):
        d = dict(
            n_docs=len(d_list),
            n_docs_with_pdfs=len([d for d in d_list if d["n_pdfs"] > 0]),
            n_pdfs=sum(d["n_pdfs"] for d in d_list),
            total_file_size=Directory(
                AbstractDocDownloader.DIR_TEMP_DATA
            ).size,
        )
        log.debug(f"{d=}")

        for json_path in [
            AbstractDocDownloader.DATA_SUMMARY_JSON_PATH,
            AbstractDocDownloader.TEMP_DATA_SUMMARY_JSON_PATH,
        ]:
            JSONFile(json_path).write(d)
            log.info(f"Wrote {json_path}")

    @staticmethod
    def summarize_temp_data():
        d_list = AbstractDocDownloader.__get_temp_data_d_list__()
        AbstractDocDownloader.build_json(d_list)

    @staticmethod
    @cache
    def get_temp_data_summary():
        assert os.path.exists(AbstractDocDownloader.DATA_SUMMARY_JSON_PATH)
        return JSONFile(AbstractDocDownloader.DATA_SUMMARY_JSON_PATH).read()

    @staticmethod
    def back_compress():
        for pdf_file_path in AbstractDocDownloader.__gen_pdf_file_paths__():
            PDF.compress(pdf_file_path, pdf_file_path)
