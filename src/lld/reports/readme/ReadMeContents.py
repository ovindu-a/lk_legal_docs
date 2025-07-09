import os
import shutil

from utils import File

from lld.docs import DocFactory


class ReadMeContents:
    DIR_README = "readme"

    @staticmethod
    def __build_contents__(label, x, doc_list_for_x, display_key):

        contents_path = os.path.join(
            ReadMeContents.DIR_README, f"contents-{label}-{x}.md"
        )
        n = len(doc_list_for_x)

        lines = [f"# {display_key}", "", f"**{n:,}** Documents", ""]
        for i_doc, doc in enumerate(doc_list_for_x, start=1):
            lines.append(
                f"- {
                    doc.get_emoji()} [{
                    doc.date}] [{
                    doc.description}]({
                    doc.remote_data_url})"
            )
            if i_doc % 10 == 0:
                lines.extend(["", "---", ""])
        lines.append("")
        File(contents_path).write("\n".join(lines))
        return contents_path

    @staticmethod
    def __get_contents_by_x__(label, func_get_key, func_get_display_key=None):
        func_get_display_key = func_get_display_key or func_get_key

        x_to_doc_list = DocFactory.x_to_list_all(func_get_key)
        title_str = label.replace("-", " ").title()
        lines = [f"### By {title_str}", ""]
        for x, doc_list_for_x in x_to_doc_list.items():
            display_key = func_get_display_key(doc_list_for_x[0])
            url = ReadMeContents.__build_contents__(
                label, x, doc_list_for_x, display_key
            )
            lines.append(f"- [{display_key}]({url})")
        lines.append("")
        return lines

    def get_lines_for_contents(self):
        if not os.path.exists(ReadMeContents.DIR_README):
            shutil.rmtree(ReadMeContents.DIR_README, ignore_errors=True)
        os.makedirs(ReadMeContents.DIR_README, exist_ok=True)
        return (
            ["## Contents", ""]
            + ReadMeContents.__get_contents_by_x__(
                "document-type",
                lambda doc: doc.get_doc_type_name(),
                lambda doc: doc.get_doc_type_name_long_with_emoji(),
            )
            + ReadMeContents.__get_contents_by_x__(
                "year", lambda doc: doc.year
            )
        )
