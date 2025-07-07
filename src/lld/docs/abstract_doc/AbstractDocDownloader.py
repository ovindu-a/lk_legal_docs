import os

from lld.www_common import WebPage


class AbstractDocDownloader:

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
