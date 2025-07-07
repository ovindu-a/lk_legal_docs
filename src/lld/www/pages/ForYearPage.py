from utils import Log

from lld.www_common import WebPage
from utils_future import Lang

log = Log("ForYearPage")


class ForYearPage(WebPage):
    @staticmethod
    def __get_base_url__(doc_cls):
        return "/".join(
            [WebPage.BASE_URL, "view", doc_cls.get_doc_type_name()]
        )

    def __init__(self, url, doc_cls):
        super().__init__(url)
        self.doc_cls = doc_cls

    @staticmethod
    def parse_lang_to_source_url(base_url, a_list):
        source_urls = {}
        for a in a_list:
            if a.has_attr("disabled"):
                continue
            url = "/".join(
                [
                    base_url,
                    a["href"],
                ]
            )

            for lang in Lang.list_all():
                if url.endswith(lang.pdf_code):
                    source_urls[lang.code] = url

        return source_urls

    def __parse_tr__(self, tr):
        td_list = tr.find_all("td")
        doc_num = td_list[0].text.strip()
        date = td_list[1].text.strip()
        description = td_list[2].text.strip()
        url_td = td_list[3]
        a_list = url_td.find_all("a")
        lang_to_source_url = self.parse_lang_to_source_url(
            ForYearPage.__get_base_url__(self.doc_cls), a_list
        )

        return self.doc_cls(
            doc_num=doc_num,
            date=date,
            description=description,
            lang_to_source_url=lang_to_source_url,
        )

    def gen_docs(self):

        table = self.soup.find(
            "table", class_="table table-bordered table-striped table-hover"
        )
        tbody = table.find("tbody")

        for tr in tbody.find_all("tr"):
            doc = self.__parse_tr__(tr)
            if not doc:
                continue
            yield doc
