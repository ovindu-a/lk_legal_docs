import os
import shutil
import sys
import time

from utils import Log

from lld import AbstractDoc, DocFactory

DEFAULT_MAX_DELTA_T = 600
GIT_REPO_URL = "https://github.com/nuuuwan/lk_legal_docs_data.git"

log = Log("pdf_downloader")


def __testing_git_clone__():
    dir_temp_data = AbstractDoc.DIR_TEMP_DATA
    if os.path.exists(dir_temp_data):
        shutil.rmtree(dir_temp_data, ignore_errors=True)
    os.makedirs(dir_temp_data, exist_ok=True)
    os.system(f"git clone {GIT_REPO_URL} {dir_temp_data}")


def downloader(max_delta_t):
    log.debug(f"{max_delta_t=}")

    assert os.path.exists(AbstractDoc.DIR_TEMP_DATA)

    t_start = time.time()
    doc_list = DocFactory.list_all()
    for doc in doc_list:
        doc.download_all()

        delta_t = time.time() - t_start
        log.info(f"[{delta_t:.1f}s]" + f" Downloaded pdfs for {doc.id}")
        if delta_t > max_delta_t:
            log.warning(
                f"⛔️ Stopping. ⏰ {delta_t:.1f}s > {max_delta_t:.1f}s."
            )
            return

    log.info("⛔️🛑 Downloaded ALL pdfs.")
    return


def main(max_delta_t):
    # __testing_git_clone__()
    downloader(max_delta_t)

    AbstractDoc.summarize_temp_data()


if __name__ == "__main__":
    main(
        max_delta_t=(
            int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_DELTA_T
        )
    )
