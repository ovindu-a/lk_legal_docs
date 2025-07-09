import random
import re

from utils import Log

from lld.docs.custom_docs.Gazette import Gazette
from lld.www.pages import AbstractScraper
from lld.www.pages.ForYearPage import ForYearPage
from lld.www_common import WebPage

log = Log("GazettePages")


class GazettePages(AbstractScraper):

    BASE_URL = "https://documents.gov.lk/view/gazettes"

    def get_metadata_scraper_name(self):
        return "gazettes"

    def gen_year_pages(self, traverse_random):
        by_year_page = WebPage(GazettePages.BASE_URL + "/find_gazette.html")
        div_year_container = by_year_page.soup.find(
            "div", class_="year-container"
        )
        a_list = div_year_container.find_all("a")
        if traverse_random:

            random.shuffle(a_list)
        for a in a_list:
            url = "/".join([GazettePages.BASE_URL, a["href"]])
            yield WebPage(url)

    def gen_gazette_pages(self, traverse_random):
        for year_page in self.gen_year_pages(traverse_random):
            table = year_page.soup.find("table", class_="table")
            tbody = table.find("tbody")
            for tr in tbody.find_all("tr"):
                td_list = tr.find_all("td")
                a = td_list[1].find("a")
                url = "/".join([GazettePages.BASE_URL, a["href"]])
                yield WebPage(url)

    @staticmethod
    def __get_doc_num__(date, description):
        doc_num = re.sub(r"[^a-zA-Z0-9]+", "-", description).lower()
        doc_num = f"{date}-{doc_num}"
        doc_num = re.sub(r"-{2,}", "-", doc_num)
        return doc_num

    @staticmethod
    def __process_li__(li_sub_part, date):
        description = li_sub_part.find("strong").text.strip()
        doc_num = GazettePages.__get_doc_num__(date, description)

        lang_to_source_url = ForYearPage.parse_lang_to_source_url(
            GazettePages.BASE_URL, li_sub_part.find_all("a")
        )

        return Gazette(
            doc_num=doc_num,
            date=date,
            description=description,
            lang_to_source_url=lang_to_source_url,
        )

    def gen_docs(self, traverse_random):
        for gazette_page in self.gen_gazette_pages(traverse_random):
            date = gazette_page.url.split("/")[-1].split(".")[0]
            assert len(date) == 10

            part_cards = gazette_page.soup.find_all("div", class_="part-card")
            for part_card in part_cards:
                ul_sub_parts = part_card.find("ul", class_="list-group")
                for li_sub_part in ul_sub_parts.find_all(
                    "li", class_="list-group-item"
                ):
                    doc = GazettePages.__process_li__(li_sub_part, date)
                    if doc:
                        yield doc
