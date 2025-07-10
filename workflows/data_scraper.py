import os
import sys
import time

from utils import Log, Parallel

from lld import AbstractDoc, DocFactory

DEFAULT_MAX_DELTA_T = 15 * 60


log = Log("data_scraper")
N_BATCH = 4


def main(max_delta_t):
    log.debug(f"{max_delta_t=}")

    assert os.path.exists(AbstractDoc.DIR_TEMP_DATA)

    t_start = time.time()
    doc_list = DocFactory.list_all()
    n_doc_list = len(doc_list)
    log.debug(f"{n_doc_list=}")

    i_doc = 0

    while i_doc < n_doc_list:
        workers = []
        for j in range(N_BATCH):
            if i_doc >= n_doc_list:
                break
            doc = doc_list[i_doc]

            def worker(doc):
                doc.copy_metadata_to_temp_data()
                doc.download_all_pdfs()
                doc.extract_text()
                return True

            workers.append(worker(doc=doc))

        Parallel.run(
            workers,
            max_threads=N_BATCH,
        )

        delta_t = time.time() - t_start
        log.debug(f"{delta_t=:,.1f}s")
        if delta_t > max_delta_t:
            log.warning(
                f"⛔️ Stopping. ⏰ {delta_t:.1f}s > {max_delta_t:.1f}s."
            )
            return

    log.info("⛔️🛑 Downloaded ALL pdfs.")
    return


if __name__ == "__main__":
    main(
        max_delta_t=(
            int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MAX_DELTA_T
        )
    )
