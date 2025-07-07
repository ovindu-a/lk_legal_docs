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
        self.total_data_size_m = DocFactory.get_total_data_size() / 1_000_000.0
        self.html_cache_size_m = WebPage.get_html_cache_size() / 1_000_000.0
        dates = [doc.date for doc in self.doc_list]
        self.min_date = min(dates)
        self.max_date = max(dates)

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
    def get_source_md(doc):
        parts = []
        for lang in Lang.list_all():
            if lang.code in doc.lang_to_source_url:
                url = doc.lang_to_source_url[lang.code]
                parts.append(f"[`{lang.short_name}`]({url})")
        return " ".join(parts)

    @staticmethod
    def get_d_list(doc_list):
        d_list = []
        for doc in doc_list:
            d = dict(
                type=doc.get_emoji(),
                date=doc.date,
                title=doc.description_cleaned,
                sources=ReadMe.get_source_md(doc),
                doc_num=f"[{doc.doc_num}]({doc.dir_data})",
            )
            d_list.append(d)
        return d_list

    @staticmethod
    def __get_lines_for_docs__(title, doc_list, n_sample):
        n = len(doc_list)
        sampled_doc_list = ReadMe.__sample__(doc_list, n_sample)
        d_list = ReadMe.get_d_list(sampled_doc_list)
        return (
            [title, ""]
            + Markdown.table(d_list)
            + [
                "",
                f"*(Uniformly Spaced Sample of {n_sample:,} from {n:,})*",
                "",
            ]
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
            image_path, lines_stat_sig = chart.draw_chart()
            lines.extend(
                [f"![Coverage Chart-{t_label.title()}]({image_path})", ""]
            )
            # lines.extend(lines_stat_sig + [""])

        return lines

    def get_lines_for_system_info(self):
        lines = [
            "## Pipeline Information",
            "",
            f"- HTML-Cache = {self.html_cache_size_m:.1f} MB ",
            "",
        ]
        return lines

    def get_lines(self):
        n = len(self.doc_list)
        doc_name_list = ", ".join(
            doc_cls.get_doc_type_name_long_with_emoji()
            for doc_cls in DocFactory.cls_list_all()
        )
        return (
            [
                "# Legal Documents - #SriLanka 🇱🇰",
                "",
                f"*Last Updated **{self.time_str}**.*",
                "",
                f"**{n:,}** documents ({self.total_data_size_m:.1f} MB),"
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
            + self.get_lines_summary_statistics()
            + self.get_lines_summary_charts()
            + self.get_lines_for_sample_docs()
            + self.get_lines_for_interesting_docs()
            + self.get_lines_for_system_info()
        )

    def build(self):
        lines = self.get_lines()
        File(self.PATH).write("\n".join(lines))
        log.debug(f"Wrote {len(lines)} lines to {self.PATH}.")
