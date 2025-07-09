import os
import re
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from utils_future import Lang


@dataclass
class AbstractDocBase:
    doc_num: str
    date: str
    description: str
    lang_to_source_url: dict[str, str]

    DIR_DATA = "data"

    @cached_property
    def datetime(self):
        return datetime.strptime(self.date, "%Y-%m-%d")

    @cached_property
    def year(self):
        return self.datetime.strftime("%Y")

    @cached_property
    def year_and_month(self):
        return self.datetime.strftime("%Y-%m")

    @cached_property
    def month_only(self):
        return self.datetime.strftime("%m-%b")

    @cached_property
    def date_only(self):
        return self.datetime.strftime("%d")

    @cached_property
    def decade(self):
        return self.year[:3] + "0s"

    @cached_property
    def weekday(self):
        return self.datetime.strftime("%u-%a")

    @cached_property
    def id(self):
        return self.doc_num.replace("/", "-")

    @classmethod
    def get_doc_type_dir(cls):
        return os.path.join(cls.DIR_DATA, cls.get_doc_type_name())

    def has_sources(self):
        return len(self.lang_to_source_url) > 0

    @cached_property
    def language_coverage_code(self):
        covered_langs = []
        for lang in Lang.list_all():
            if lang.code in self.lang_to_source_url:
                covered_langs.append(lang.code)

        n = len(covered_langs)
        return f"{n}-" + "+".join(covered_langs)

    @cached_property
    def description_cleaned(self):
        x = re.sub(r"[^A-Za-z0-9\s]", "", self.description).strip()
        x = re.sub(r"\s+", " ", x)
        if len(x) > 253:
            x = x[:253] + "..."
        return x
