from functools import cache, cached_property


class Lang:
    def __init__(self, code_iso_639_1: str):
        assert len(code_iso_639_1) == 2
        assert code_iso_639_1.isalpha() and code_iso_639_1.islower()
        self.code = code_iso_639_1

    @cached_property
    def long_name(self):
        return {
            "si": "සිංහල",
            "ta": "தமிழ்",
            "en": "English",
        }.get(self.code, self.code + "-Language")

    @cached_property
    def short_name(self):
        return {
            "si": "සි",
            "ta": "த",
            "en": "E",
        }.get(self.code, self.code)

    @cached_property
    def pdf_code(self):
        return self.code[0].upper() + ".pdf"

    @staticmethod
    @cache
    def list_all():
        return [
            Lang("si"),
            Lang("ta"),
            Lang("en"),
        ]
