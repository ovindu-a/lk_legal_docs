import os

from utils import File

from lld.docs import DocFactory


class ReadMeContents:
    DIR_README = "readme"

    @staticmethod
    def __build_contents__(label, x, doc_list_for_x):
        os.makedirs(ReadMeContents.DIR_README, exist_ok=True)
        contents_path = os.path.join(
            ReadMeContents.DIR_README, f"contents-{label}-{x}.md"
        )
        n = len(doc_list_for_x)
        lines = [f"# {x} ({n:,} Documents)", ""]
        for doc in doc_list_for_x:
            lines.append(
                f"- [{doc.date}] [{doc.description}]({doc.remote_data_url})"
            )
        lines.append("")
        File(contents_path).write("\n".join(lines))
        return contents_path

    @staticmethod
    def __get_contents_by_x__(label, func_get_key):
        x_to_doc_list = DocFactory.x_to_list_all(func_get_key)
        title_str = label.replace("-", " ").title()
        lines = [f"### By {title_str}", ""]
        for x, doc_list_for_x in x_to_doc_list.items():
            url = ReadMeContents.__build_contents__(label, x, doc_list_for_x)
            lines.append(f"- [{x}]({url})")
        lines.append("")
        return lines

    def get_lines_for_contents(self):
        return (
            ["## Contents", ""]
            + ReadMeContents.__get_contents_by_x__(
                "document-type",
                lambda doc: doc.get_doc_type_name_long_with_emoji(),
            )
            + ReadMeContents.__get_contents_by_x__(
                "year", lambda doc: doc.year
            )
        )
