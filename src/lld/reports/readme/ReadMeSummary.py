import shutil

from lld.docs import DocFactory
from lld.reports.ChartDocumentCountByTime import ChartDocumentCountByTime
from utils_future import Markdown


class ReadMeSummary:
    def get_doc_legend(self):
        doc_cls_list = DocFactory.cls_list_all()
        inner = ", ".join(
            f"{doc_cls.get_emoji()} = {doc_cls.get_doc_type_name_long()}"
            for doc_cls in doc_cls_list
        )
        return f"({inner})"

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
