import os

from lld import AbstractDoc, DocFactory
from utils_future import Git

GIT_REPO_URL = "https://github.com/nuuuwan/lk_legal_docs_data.git"


def main():
    git = Git(AbstractDoc.DIR_TEMP_DATA)
    if not os.path.exists(AbstractDoc.DIR_TEMP_DATA):
        git.clone(GIT_REPO_URL)
    # else:
    #     git.pull()

    # AbstractDoc.back_compress()
    doc_list = DocFactory.list_all()
    for doc in doc_list:
        doc.copy_metadata_to_temp_data()

    git.add(".").commit("back-compressed pdfs")
    git.pull()
    git.push()


if __name__ == "__main__":
    main()
