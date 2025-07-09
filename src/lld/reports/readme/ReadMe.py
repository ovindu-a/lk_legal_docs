from utils import File, Log, Time, TimeFormat

from lld.docs import DocFactory
from lld.reports.readme.ReadMeContents import ReadMeContents
from lld.reports.readme.ReadMeDocs import ReadMeDocs
from lld.reports.readme.ReadMeSummary import ReadMeSummary
from lld.www_common import WebPage

log = Log("ReadMe")


class ReadMe(ReadMeDocs, ReadMeSummary, ReadMeContents):
    PATH = "README.md"

    def __init__(self):
        self.time_str = TimeFormat.TIME.format(Time.now())
        self.doc_list = DocFactory.list_all()
        self.n_docs = len(self.doc_list)
        self.total_data_size_m = (
            DocFactory.get_total_data_size() / 1_000_000.0
        )
        self.html_cache_size_m = WebPage.get_html_cache_size() / 1_000_000.0
        dates = [doc.date for doc in self.doc_list]
        self.min_date = min(dates)
        self.max_date = max(dates)
        self.temp_data_summary = DocFactory.get_temp_data_summary()

    def get_lines_for_temp_data(self):
        n_pdfs = self.temp_data_summary["n_pdfs"]
        n_docs_with_pdfs = self.temp_data_summary["n_docs_with_pdfs"]
        total_file_size_g = (
            self.temp_data_summary["total_file_size"] / 1_000_000_000.0
        )
        p_docs = n_docs_with_pdfs / self.n_docs
        final_file_size_g = total_file_size_g / p_docs

        return [
            f"📄 Currently, {n_pdfs:,} PDFs ({total_file_size_g:.1f} GB)"
            + f" for **{n_docs_with_pdfs:,}** documents ({p_docs:.1%})"
            + " have been downloaded."
            + " Final data size is estimated to be "
            + f"~{final_file_size_g:.0f} GB.",
            "",
        ]

    def get_lines(self):
        doc_name_list = ", ".join(
            doc_cls.get_doc_type_name_long_with_emoji()
            for doc_cls in DocFactory.cls_list_all()
        )
        return (
            [
                "# #SriLanka 🇱🇰 - Legal Documents #Dataset",
                "",
                f"*Last Updated **{self.time_str}**.*",
                "",
                f"**{self.n_docs:,}** documents"
                + f" ({self.total_data_size_m:.1f} MB),"
                + f" from {self.min_date} to {self.max_date}.",
                "",
                "A collection of"
                + f" {doc_name_list} and more, "
                + " from [documents.gov.lk](https://documents.gov.lk).",
                "",
                "🆓 **Public** data, fully open-source – fork freely!",
                "",
                "🗣️ **Tri-Lingual** - සිංහල, தமிழ் & English",
                "",
                "🔍 **Useful** for Journalists, Researchers,"
                + " Lawyers & law students,"
                + " Policy watchers & Citizens who want to stay informed",
                "",
                "#Legal #OpenData #GovTech",
                "",
            ]
            + self.get_lines_for_temp_data()
            + self.get_lines_summary_statistics()
            + self.get_lines_summary_charts()
            + self.get_lines_for_contents()
            + self.get_lines_for_latest_docs()
            + self.get_lines_for_sample_docs()
            + self.get_lines_for_interesting_docs()
        )

    def build(self):
        lines = self.get_lines()
        File(self.PATH).write("\n".join(lines))
        log.debug(f"Wrote {len(lines)} lines to {self.PATH}.")
