import os
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
        assert data["doc_type_name"] == cls.get_doc_type_name()
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
