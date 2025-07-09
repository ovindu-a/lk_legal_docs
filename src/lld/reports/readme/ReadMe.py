import os
import shutil

from utils import File, Log, Time, TimeFormat

from lld.docs import DocFactory
from lld.reports.ChartDocumentCountByTime import ChartDocumentCountByTime
from lld.www_common import WebPage
from utils_future import Lang, Markdown

log = Log("ReadMe")


class ReadMe:
    PATH = "README.md"

    def __init__(self):
        self.time_str = TimeFormat.TIME.format(Time.now())
        self.doc_list = DocFactory.list_all()
        self.n_docs = len(self.doc_list)
        self.total_data_size_m = DocFactory.get_total_data_size() / 1_000_000.0
        self.html_cache_size_m = WebPage.get_html_cache_size() / 1_000_000.0
        dates = [doc.date for doc in self.doc_list]
        self.min_date = min(dates)
        self.max_date = max(dates)
        self.temp_data_summary = DocFactory.get_temp_data_summary()

    def get_doc_legend(self):
        doc_cls_list = DocFactory.cls_list_all()
        inner = ", ".join(
            f"{doc_cls.get_emoji()} = {doc_cls.get_doc_type_name_long()}"
            for doc_cls in doc_cls_list
        )
        return f"({inner})"

    @staticmethod
    def __sample__(items, n_document_display):
        n = len(items)
        sampled_items = []
        for i in range(0, n_document_display + 1):
            j = int((n - 1) * i / n_document_display)
            item = items[j]
            sampled_items.append(item)
        return sampled_items

    @staticmethod
    def get_data(doc):
        parts = []

        for lang in Lang.list_all():
            if lang.code in doc.lang_to_source_url:
                source_url = doc.lang_to_source_url.get(lang.code)
                parts.append(f"[`{lang.short_name}-src`]({source_url})")

                pdf_path = doc.get_pdf_path(lang.code)
                if os.path.exists(pdf_path):
                    remote_pdf_path = doc.get_remote_pdf_path(lang.code)
                    parts.append(
                        f"[`{lang.short_name}-pdf`]({remote_pdf_path})"
                    )

                txt_path = doc.get_txt_path(lang.code)
                if os.path.exists(txt_path):
                    remote_txt_path = doc.get_remote_txt_path(lang.code)
                    parts.append(
                        f"[`{lang.short_name}-txt`]({remote_txt_path})"
                    )
                parts.append("<br/>")

        parts.append(f"[`metadata`]({doc.get_remote_metadata_path()})")
        parts.append(f"[`all`]({doc.remote_data_url})")

        return " ".join(parts)

    @staticmethod
    def get_d_list(doc_list):
        d_list = []
        for doc in doc_list:
            d = dict(
                type=doc.get_emoji(),
                date=doc.date,
                title=doc.description_cleaned,
                data=ReadMe.get_data(doc),
            )
            d_list.append(d)
        return d_list

    @staticmethod
    def __get_lines_for_docs__(title, doc_list, n_sample):
        n = len(doc_list)
        if n > n_sample:
            sampled_doc_list = ReadMe.__sample__(doc_list, n_sample)
        else:
            sampled_doc_list = doc_list

        d_list = ReadMe.get_d_list(sampled_doc_list)
        footer_lines = [""]
        if n > n_sample:
            footer_lines = [
                "",
                f"*(Uniformly Spaced Sample of {n_sample:,} from {n:,})*",
                "",
            ]

        return [title, ""] + Markdown.table(d_list) + footer_lines

    def get_lines_for_latest_docs(self):
        return ReadMe.__get_lines_for_docs__(
            "## Latest Documents", self.doc_list[:30], n_sample=30
        )

    def get_lines_for_sample_docs(self):
        return ReadMe.__get_lines_for_docs__(
            "## All Documents", self.doc_list, n_sample=30
        )

    def get_sunday_docs(self):
        return [doc for doc in self.doc_list if doc.weekday == "7-Sun"]

    def get_lines_for_interesting_docs(self):
        lines = [
            "## Interesting Documents",
            "",
        ] + ReadMe.__get_lines_for_docs__(
            "### Documents Published on a Sunday",
            self.get_sunday_docs(),
            n_sample=10,
        )
        return lines

    def get_summary_statistics(self):
        d_list = []

        doc_type_to_doc_list = {}
        for doc in self.doc_list:
            doc_type = doc.get_doc_type_name_long_with_emoji()
            if doc_type not in doc_type_to_doc_list:
                doc_type_to_doc_list[doc_type] = []
            doc_type_to_doc_list[doc_type].append(doc)

        for doc_type, doc_list in doc_type_to_doc_list.items():
            n = len(doc_list)
            dates = [doc.date for doc in doc_list]
            min_date = min(dates)
            max_date = max(dates)
            d = dict(
                doc_type=doc_type,
                n=f"{n:,}",
                min_date=min_date,
                max_date=max_date,
            )
            d_list.append(d)
        return d_list

    def get_lines_summary_statistics(self):
        lines = [
            "## Summary Statistics",
            "",
        ]
        d_list = self.get_summary_statistics()
        lines.extend(Markdown.table(d_list) + [""])
        return lines

    def get_lines_summary_charts(self):
        shutil.rmtree("images", ignore_errors=True)
        lines = ["## Summary Charts", ""]
        for func_get_t, t_label, func_filter_documents in [
            (
                lambda doc: doc.date,
                "last-week",
                lambda doc: doc.age_days <= 7,
            ),
            (lambda doc: doc.year, "year", None),
            (
                lambda doc: doc.language_coverage_code,
                "language-coverage",
                None,
            ),
            (lambda doc: doc.weekday, "weekday", None),
        ]:
            chart = ChartDocumentCountByTime(
                self.doc_list, func_get_t, t_label, func_filter_documents
            )
            image_path, _ = chart.draw_chart()
            lines.extend(
                [f"![Coverage Chart-{t_label.title()}]({image_path})", ""]
            )
        return lines

    def get_lines_for_system_info(self):
        lines = [
            "## metadata_scraper Information",
            "",
            f"- HTML-Cache = {self.html_cache_size_m:.1f} MB ",
            "",
        ]
        return lines

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
            + self.get_lines_for_latest_docs()
            + self.get_lines_for_sample_docs()
            + self.get_lines_for_interesting_docs()
            + self.get_lines_for_system_info()
        )

    def build(self):
        lines = self.get_lines()
        File(self.PATH).write("\n".join(lines))
        log.debug(f"Wrote {len(lines)} lines to {self.PATH}.")
