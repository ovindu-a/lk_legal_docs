import random

from utils import Log

from lld.www.pages.Abstractmetadata_scraper import Abstractmetadata_scraper
from lld.www.pages.ForYearPage import ForYearPage
from lld.www.pages.GazettePages import GazettePages
from lld.www_common import WebPage

log = Log("ByYearPage")


class ByYearPage(WebPage, Abstractmetadata_scraper):

    def get_metadata_scraper_name(self):
        return self.doc_cls.get_doc_type_name()

    @staticmethod
    def __get_url__(doc_cls):
        return "/".join(
            [
                ForYearPage.__get_base_url__(doc_cls),
                doc_cls.get_doc_type_name_short() + ".html",
            ]
        )

    def __init__(self, doc_cls):
        super().__init__(ByYearPage.__get_url__(doc_cls))
        self.doc_cls = doc_cls

    def gen_for_year_pages(self, traverse_random):
        div_buttons = self.soup.find("div", class_="button-container")
        if not div_buttons:
            return
        a_list = div_buttons.find_all("a")
        if traverse_random:
            random.shuffle(a_list)
        for a in a_list:
            url = "/".join(
                [ForYearPage.__get_base_url__(self.doc_cls), a["href"]]
            )
            yield ForYearPage(url, self.doc_cls)

    def gen_docs(self, traverse_random):
        for for_year_page in self.gen_for_year_pages(traverse_random):
            for doc in for_year_page.gen_docs():
                yield doc

    def run_metadata_scraper(self, max_n_hot, traverse_random):
        if self.doc_cls.get_doc_type_name() == "gazettes":
            return GazettePages().run_metadata_scraper(
                max_n_hot, traverse_random
            )
        return super().run_metadata_scraper(max_n_hot, traverse_random)
