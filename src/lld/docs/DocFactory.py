import os
from functools import cache

from utils import JSONFile, Log, TSVFile

from lld.docs.abstract_doc import AbstractDoc
from lld.docs.custom_docs import Act, Bill, ExtraGazette, Gazette
from utils_future import Directory

log = Log("DocFactory")


class DocFactory:
    ALL_TSV_PATH = os.path.join(AbstractDoc.DIR_DATA, "all.tsv")
    N_LATEST = 100
    LATEST_TSV_PATH = os.path.join(
        AbstractDoc.DIR_DATA, f"latest-{N_LATEST}.tsv"
    )

    @staticmethod
    def cls_list_all():
        return [
            Gazette,
            ExtraGazette,
            Act,
            Bill,
        ]

    @staticmethod
    def cls_from_doc_type(doc_type):
        doc_type = doc_type.lower()
        for doc_cls in DocFactory.cls_list_all():
            if doc_cls.get_doc_type_name() == doc_type:
                return doc_cls
        raise ValueError(f"Unknown doc type: {doc_type}")

    @staticmethod
    def from_dict_flat(data):
        cls = DocFactory.cls_from_doc_type(data["doc_type_name"])
        return cls.from_dict_flat(data)

    @staticmethod
    def from_dict(data):
        cls = DocFactory.cls_from_doc_type(data["doc_type_name"])
        return cls.from_dict(data)

    @staticmethod
    def from_file(file_path):
        assert file_path.endswith(".json")
        data = JSONFile(file_path).read()
        return DocFactory.from_dict(data)

    @classmethod
    def __get_metadata_file_path_lists__(cls):
        file_path_lists = []
        for dir_path, _, file_names in os.walk(AbstractDoc.DIR_DATA):
            for file_name in file_names:
                if file_name == "metadata.json":
                    file_path = os.path.join(dir_path, file_name)
                    file_path_lists.append(file_path)
        return file_path_lists

    @staticmethod
    def __list_all_from_metadata_files__():
        doc_list = []
        for (
            metadata_file_path
        ) in DocFactory.__get_metadata_file_path_lists__():
            doc = DocFactory.from_file(metadata_file_path)
            doc_list.append(doc)

        doc_list.sort(key=lambda x: (x.date, x.doc_num), reverse=True)
        log.debug(f"Found {len(doc_list):,} docs (all types).")
        return doc_list

    @staticmethod
    def write_all():
        doc_list = DocFactory.__list_all_from_metadata_files__()
        TSVFile(DocFactory.ALL_TSV_PATH).write(
            [doc.to_dict_flat() for doc in doc_list]
        )
        n = len(doc_list)
        file_size_m = os.path.getsize(DocFactory.ALL_TSV_PATH) / (1000 * 1000)
        log.info(
            f"Wrote {n:,} docs to"
            + f" {DocFactory.ALL_TSV_PATH} ({file_size_m:.2f} MB)"
        )

    @staticmethod
    def write_latest():
        doc_list = DocFactory.list_all()[: DocFactory.N_LATEST]
        TSVFile(DocFactory.LATEST_TSV_PATH).write(
            [doc.to_dict_flat() for doc in doc_list]
        )
        n = len(doc_list)
        file_size_m = os.path.getsize(DocFactory.LATEST_TSV_PATH) / (
            1000 * 1000
        )
        log.info(
            f"Wrote {n:,} docs to"
            + f" {DocFactory.LATEST_TSV_PATH} ({file_size_m:.2f} MB)"
        )

    @staticmethod
    @cache
    def list_all():
        assert os.path.exists(DocFactory.ALL_TSV_PATH)
        d_list = TSVFile(DocFactory.ALL_TSV_PATH).read()
        doc_list = [DocFactory.from_dict_flat(d) for d in d_list]
        doc_list.sort(key=lambda x: (x.date, x.doc_num), reverse=True)
        return doc_list

    @staticmethod
    def get_total_data_size():
        return Directory(AbstractDoc.DIR_DATA).size

    @staticmethod
    def build_temp_data_summary():
        doc_list = DocFactory.list_all()
        d = dict(
            n_docs=len(doc_list),
            n_docs_with_pdfs=len([d for d in doc_list if d.n_pdfs > 0]),
            n_pdfs=sum(d.n_pdfs for d in doc_list),
            total_file_size=Directory(AbstractDoc.DIR_TEMP_DATA).size,
        )
        log.debug(f"{d=}")

        for json_path in [
            AbstractDoc.DATA_SUMMARY_JSON_PATH,
            AbstractDoc.TEMP_DATA_SUMMARY_JSON_PATH,
        ]:
            JSONFile(json_path).write(d)
            log.info(f"Wrote {json_path}")

    @staticmethod
    @cache
    def get_temp_data_summary():
        assert os.path.exists(AbstractDoc.DATA_SUMMARY_JSON_PATH)
        return JSONFile(AbstractDoc.DATA_SUMMARY_JSON_PATH).read()
