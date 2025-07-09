from utils import Log

from lld.docs.abstract_doc.AbstractDocBase import AbstractDocBase
from lld.docs.abstract_doc.AbstractDocDownloader import AbstractDocDownloader
from lld.docs.abstract_doc.AbstractDocExtractText import AbstractDocExtractText
from lld.docs.abstract_doc.AbstractDocSerializer import AbstractDocSerializer

log = Log("AbstractDoc")


class AbstractDoc(
    AbstractDocBase,
    AbstractDocSerializer,
    AbstractDocDownloader,
    AbstractDocExtractText,
):

    @classmethod
    def get_doc_type_name(cls):
        raise NotImplementedError

    @classmethod
    def get_doc_type_name_short(cls):
        raise NotImplementedError

    @classmethod
    def get_doc_type_name_long(cls):
        return cls.get_doc_type_name().title()

    @classmethod
    def get_emoji(cls):
        raise NotImplementedError

    @classmethod
    def get_doc_type_name_long_with_emoji(cls):
        return f"{cls.get_emoji()} {cls.get_doc_type_name_long()}"
