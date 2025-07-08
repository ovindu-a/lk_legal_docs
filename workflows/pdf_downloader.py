import os
import sys
import time

from utils import Log

from lld import AbstractDoc, DocFactory, ReadMe
from workflows.scraper import git_rebase

DEFAULT_MAX_DELTA_T = 600


log = Log("pdf_downloader")


def downloader(max_delta_t):
    log.debug(f"{max_delta_t=}")

    assert os.path.exists(AbstractDoc.DIR_TEMP_DATA)

    t_start = time.time()
    doc_list = DocFactory.list_all()

    for doc in doc_list:
        doc.copy_metadata_to_temp_data()

    for doc in doc_list:
        doc.download_all()
        doc.extract_text()

        delta_t = time.time() - t_start
        if delta_t > max_delta_t:
            log.warning(
                f"⛔️ Stopping. ⏰ {delta_t:.1f}s > {max_delta_t:.1f}s."
            )
            return

    log.info("⛔️🛑 Downloaded ALL pdfs.")
    return


def main(max_delta_t):
    downloader(max_delta_t)
    git_rebase(AbstractDoc.DIR_TEMP_DATA)
    git_rebase(".")
    AbstractDoc.summarize_temp_data()
    ReadMe().build()


if __name__ == "__main__":
    main(
        max_delta_t=(
            int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_DELTA_T
        )
    )
