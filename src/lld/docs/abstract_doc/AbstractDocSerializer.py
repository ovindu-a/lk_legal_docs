import os
import tempfile
from functools import cached_property

from utils import JSONFile, Log

from utils_future import Lang

log = Log("AbstractDocSerializer")


class AbstractDocSerializer:
    @cached_property
    def dir_data(self):
        dir_data = os.path.join(self.get_doc_type_dir(), self.year, self.id)
        return dir_data

    @cached_property
    def dir_temp_data(self):
        return os.path.join(
            tempfile.gettempdir(), "lk_legal_docs_data", self.dir_data
        )

    @cached_property
    def metadata_file_path(self):
        return os.path.join(self.dir_data, "metadata.json")

    def to_dict(self):
        return dict(
            # properties (1)
            doc_type_name=self.get_doc_type_name(),
            # attributes
            date=self.date,
            description=self.description,
            lang_to_source_url=self.lang_to_source_url,
            doc_num=self.doc_num,
            # properties (2)
            id=self.id,
            dir_data=self.dir_data,
        )

    def to_dict_flat(self):
        d = dict(
            # properties (1)
            doc_type_name=self.get_doc_type_name(),
            # attributes (1)
            date=self.date,
            description=self.description,
        )
        for lang in Lang.list_all():
            source_url = self.lang_to_source_url.get(lang.code, "None")
            d["source_url_" + lang.code] = source_url

        d |= dict(
            # attributes (2)
            doc_num=self.doc_num,
            # properties (2)
            id=self.id,
            dir_data=self.dir_data,
        )

        return d

    @classmethod
    def from_dict_flat(cls, data):
        lang_to_source_url = {}
        for lang in Lang.list_all():
            source_url = data.get("source_url_" + lang.code)
            if source_url and source_url != "None":
                lang_to_source_url[lang.code] = source_url

        return cls.from_dict(
            data | dict(lang_to_source_url=lang_to_source_url)
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
