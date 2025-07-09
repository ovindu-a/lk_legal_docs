import os

from utils import Log

from utils_future import PDF

log = Log("AbstractDocExtractText")


class AbstractDocExtractText:

    def extract_text(self):
        for lang in self.lang_to_source_url.keys():
            self.__extract_text_for_lang__(lang)

    def get_txt_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.txt")

    def __extract_text_for_lang__(self, lang_code):
        pdf_path = self.get_pdf_path(lang_code)
        if not os.path.exists(pdf_path):
            return

        txt_path = self.get_txt_path(lang_code)
        if os.path.exists(txt_path):
            return

        PDF(pdf_path).extract_text(txt_path)
