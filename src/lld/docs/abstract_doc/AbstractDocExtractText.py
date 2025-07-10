import os

from utils import Log

from utils_future import PDF

log = Log("AbstractDocExtractText")


class AbstractDocExtractText:

    def extract_text(self):
        has_hot = False
        for lang in self.lang_to_source_url.keys():
            has_hot |= self.__extract_text_for_lang__(lang)
        return has_hot

    def get_txt_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.txt")

    def __extract_text_for_lang__(self, lang_code):
        pdf_path = self.get_pdf_path(lang_code)
        if not os.path.exists(pdf_path):
            return False

        txt_path = self.get_txt_path(lang_code)
        if os.path.exists(txt_path):
            return False

        return PDF(pdf_path).extract_text(txt_path)
