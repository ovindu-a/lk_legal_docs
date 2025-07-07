import os
import shutil
from functools import cached_property

from utils import JSONFile, Log

log = Log("AbstractDocSerializer")


class AbstractDocSerializer:
    @cached_property
    def dir_data(self):
        dir_data = os.path.join(self.get_doc_type_dir(), self.year, self.id)
        return dir_data

    @cached_property
    def metadata_file_path(self):
        return os.path.join(self.dir_data, "metadata.json")

    def to_dict(self):
        return dict(
            # properties
            doc_type_name=self.get_doc_type_name(),
            id=self.id,
            dir_data=self.dir_data,
            # attributes
            doc_num=self.doc_num,
            date=self.date,
            description=self.description,
            lang_to_source_url=self.lang_to_source_url,
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            doc_num=data["doc_num"],
            date=data["date"],
            description=data["description"],
            lang_to_source_url=data["lang_to_source_url"],
        )

    @classmethod
    def from_file(cls, file_path):
        data = JSONFile(file_path).read()
        return cls.from_dict(data)

    @classmethod
    def __get_doc_file_path_lists__(cls):
        dir_doc_type = cls.get_doc_type_dir()
        if not os.path.exists(dir_doc_type):
            return []

        file_path_lists = []
        for year in os.listdir(dir_doc_type):
            dir_data_for_year = os.path.join(dir_doc_type, year)
            for child_dir in os.listdir(dir_data_for_year):
                dir_data = os.path.join(dir_data_for_year, child_dir)
                file_path = os.path.join(dir_data, "metadata.json")

                if not os.path.exists(file_path):
                    # raise FileNotFoundError(f"{file_path} not found.")
                    shutil.rmtree(dir_data, ignore_errors=True)
                    log.warning(
                        f"[ HACK] ❌ Deleted {dir_data}. No metadata.json."
                    )
                else:
                    file_path_lists.append(file_path)
        return file_path_lists

    @classmethod
    def list_all(cls):
        doc_file_path_lists = cls.__get_doc_file_path_lists__()
        doc_doc_list = [
            cls.from_file(file_path) for file_path in doc_file_path_lists
        ]
        doc_doc_list.sort(key=lambda x: x.id, reverse=True)
        return doc_doc_list

    def write_metadata(self, force=False):
        file_path = self.metadata_file_path
        if not force and os.path.exists(file_path):
            return

        assert len(self.lang_to_source_url) > 0

        if not os.path.exists(self.dir_data):
            os.makedirs(self.dir_data, exist_ok=True)

        JSONFile(file_path).write(self.to_dict())
        log.debug(f"Wrote {file_path}")

    def is_stored_in_data(self):
        return os.path.exists(self.metadata_file_path)

    def is_hot(self):
        return self.has_sources() and not self.is_stored_in_data()
