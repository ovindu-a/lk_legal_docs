import sys

from utils import Log

from lld import ByYearPage, DocFactory, ReadMe, WebPage
from utils_future import Git

log = Log("scraper")

DEFAULT_MAX_DELTA_T = 150


def main(max_delta_t: int, traverse_random: bool, clear_html_cache: bool):
    log.debug(f"{max_delta_t=:,}s")
    log.debug(f"{traverse_random=}")
    log.debug(f"{clear_html_cache=}")

    if clear_html_cache:
        WebPage.delete_html_cache()

    name_to_n_hot = {}
    if max_delta_t > 0:
        for doc_cls in DocFactory.cls_list_all():
            n_hot = ByYearPage(doc_cls).run_scraper(
                max_delta_t, traverse_random
            )
            name = doc_cls.get_doc_type_name()
            name_to_n_hot[name] = n_hot
    log.debug(f"{name_to_n_hot=}")

    Git(".").add("data").add("images").add("README.md").commit(
        "pre-rebase"
    ).pull()
    DocFactory.write_all()
    DocFactory.write_latest()
    ReadMe().build()

    if clear_html_cache:
        WebPage.delete_html_cache()


if __name__ == "__main__":

    main(
        max_delta_t=(
            int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_DELTA_T
        ),
        traverse_random=False,
        clear_html_cache=True,
    )
