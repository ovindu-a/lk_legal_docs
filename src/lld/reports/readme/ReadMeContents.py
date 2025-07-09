import os
import shutil

from utils import File

from lld.docs import DocFactory


class ReadMeContents:
    DIR_README = "readme"

    @staticmethod
    def __build_contents_for_year__(
        label, x, doc_list_for_year, display_key, year
    ):

        contents_path = os.path.join(
            ReadMeContents.DIR_README, f"contents-{label}-{x}-{year}.md"
        )
        n = len(doc_list_for_year)

        lines = [
            f"# {display_key} - {year}",
            "",
            f"**{n:,}** Documents",
        ]
        previous_year_and_month = None
        for doc in doc_list_for_year:
            year_and_month = doc.year_and_month
            if previous_year_and_month != year_and_month:
                lines.extend(["", f"## {year_and_month}", ""])
                previous_year_and_month = year_and_month
            lines.append(
                f"- {
                    doc.get_emoji()} [{
                    doc.date}] [{
                    doc.description}]({
                    doc.remote_data_url})"
            )

        lines.append("")
        File(contents_path).write("\n".join(lines))
        return contents_path

    @staticmethod
    def __build_contents__(label, x, doc_list_for_x, display_key):
        contents_path = os.path.join(
            ReadMeContents.DIR_README, f"contents-{label}-{x}.md"
        )
        n = len(doc_list_for_x)
        lines = [f"# {display_key}", "", f"**{n:,}** Documents", ""]
        year_to_doc_list = DocFactory.x_to_list_all(
            doc_list_for_x, lambda d: d.year
        )
        for year, doc_list_for_year in year_to_doc_list.items():
            url = ReadMeContents.__build_contents_for_year__(
                label, x, doc_list_for_year, display_key, year
            )
            lines.append(f"- [{year}]({url})")

        lines.append("")
        File(contents_path).write("\n".join(lines))
        return contents_path

    def __get_contents_by_x__(
        self, label, func_get_key, func_get_display_key=None
    ):
        func_get_display_key = func_get_display_key or func_get_key

        x_to_doc_list = DocFactory.x_to_list_all(self.doc_list, func_get_key)
        title_str = label.replace("-", " ").title()
        lines = [f"### By {title_str}", ""]
        for x, doc_list_for_x in x_to_doc_list.items():
            display_key = func_get_display_key(doc_list_for_x[0])
            url = ReadMeContents.__build_contents__(
                label, x, doc_list_for_x, display_key
            )
            n = len(doc_list_for_x)
            lines.append(f"- [{display_key}]({url}) ({n:,} documents)")
        lines.append("")
        return lines

    def get_lines_for_contents(self):
        if os.path.exists(ReadMeContents.DIR_README):
            shutil.rmtree(ReadMeContents.DIR_README, ignore_errors=True)
        os.makedirs(ReadMeContents.DIR_README, exist_ok=True)
        return (
            ["## Contents", ""]
            + self.__get_contents_by_x__(
                "document-type",
                lambda doc: doc.get_doc_type_name(),
                lambda doc: doc.get_doc_type_name_long_with_emoji(),
            )
            + self.__get_contents_by_x__("decade", lambda doc: doc.decade)
        )
