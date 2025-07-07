from utils import Log

from lld.docs.custom_docs import Act, Bill, ExtraGazette, Gazette
from utils_future import Directory

log = Log("DocFactory")


class DocFactory:
    @staticmethod
    def list_all_cls():
        return [
            Gazette,
            ExtraGazette,
            Act,
            Bill,
        ]

    @staticmethod
    def list_all():
        doc_list = []
        for doc_cls in DocFactory.list_all_cls():
            doc_list.extend(doc_cls.list_all())

        doc_list.sort(key=lambda x: (x.date, x.doc_num), reverse=True)
        log.debug(f"Found {len(doc_list):,} docs (all types).")
        return doc_list

    @staticmethod
    def get_total_data_size():
        return Directory("data").size
