import os

from utils import Log

from utils_future import PDF, File

log = Log("AbstractDocExtractText")


class AbstractDocExtractText:

    def get_txt_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.txt")

    def get_fail_txt_path(self, lang_code):
        assert isinstance(lang_code, str)
        return os.path.join(self.dir_temp_data, f"{lang_code}.txt.fail")

    def __check_txt__(self, lang_code):
        txt_path = self.get_txt_path(lang_code)
        if os.path.exists(txt_path):
            return False
        fail_txt_path = self.get_fail_txt_path(lang_code)
        if os.path.exists(fail_txt_path):
            return False
        return True

    def __check_pdf__(self, lang_code):
        pdf_path = self.get_pdf_path(lang_code)
        if not os.path.exists(pdf_path):
            return False
        fail_pdf_path = self.get_fail_pdf_path(lang_code)
        if os.path.exists(fail_pdf_path):
            return False
        return True

    def __extract_text_for_lang__(self, lang_code):
        if not (
            self.__check_txt__(lang_code) and self.__check_pdf__(lang_code)
        ):
            return False

        pdf_path = self.get_pdf_path(lang_code)
        txt_path = self.get_txt_path(lang_code)
        if PDF(pdf_path).extract_text(txt_path):
            return True

        fail_txt_path = self.get_fail_txt_path(lang_code)
        File(fail_txt_path).write(self.id)
        return False

    def extract_text(self):
        has_hot = False
        for lang in self.lang_to_source_url.keys():
            has_hot |= self.__extract_text_for_lang__(lang)
        return has_hot
