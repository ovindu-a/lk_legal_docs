import os

from utils import File, Log

from utils_future import Lang

log = Log("AbstractDocReadMe")


class AbstractDocReadMe:

    @property
    def readme_lines(self):

        source_lines = []
        for lang, source_url in self.lang_to_source_url.items():
            lang_str = Lang(lang).long_name
            source_lines.append(f"- [{lang_str}]({source_url})")

        return (
            [
                f"# [{self.doc_num}] {self.description}",
                "",
                f"**Date:** {self.date}",
                "",
                "## Original Sources",
                "",
            ]
            + source_lines
            + [""]
        )

    def write_readme(self, force=False):
        readme_path = os.path.join(self.dir_data, "README.md")
        if not force and os.path.exists(readme_path):
            return
        File(readme_path).write_lines(self.readme_lines)
        log.debug(f"Wrote {readme_path}")
