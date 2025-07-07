import os
from functools import cached_property

import matplotlib.pyplot as plt
from utils import Log

log = Log("ChartDocumentCountByTime")


class ChartDocumentCountByTime:

    def __init__(
        self, doc_list, func_get_t, t_label, func_filter_documents=None
    ):
        self.func_get_t = func_get_t
        self.t_label = t_label

        self.doc_list = doc_list
        if func_filter_documents:
            self.doc_list = [
                doc for doc in self.doc_list if func_filter_documents(doc)
            ]

    @cached_property
    def x_to_type_to_n(self):
        idx = {}
        for doc in self.doc_list:
            t = self.func_get_t(doc)
            doc_type = doc.get_doc_type_name_long()

            if t not in idx:
                idx[t] = {}

            if doc_type not in idx[t]:
                idx[t][doc_type] = 0

            idx[t][doc_type] += 1
        idx = {k: v for k, v in sorted(idx.items(), key=lambda item: item[0])}
        return idx

    @staticmethod
    def get_show_ticks(dates):
        n = len(dates)
        n_display = min(12, n)
        ticks = []
        for i in range(0, n_display + 1):
            j = int(i * (n - 1) / n_display)
            ticks.append(dates[j])
        return ticks

    def __build_data__(self):
        x_to_type_to_n = self.x_to_type_to_n
        dates = sorted(x_to_type_to_n.keys())
        all_types = sorted(set(t for d in x_to_type_to_n.values() for t in d))
        type_to_counts = {t: [] for t in all_types}
        for date in dates:
            for t in all_types:
                type_to_counts[t].append(x_to_type_to_n[date].get(t, 0))

        return dates, all_types, type_to_counts

    def draw_stacked_bar_chart(self, ax, dates, all_types, type_to_counts):

        bottom = [0] * len(dates)
        for t in all_types:
            ax.bar(
                dates,
                type_to_counts[t],
                bottom=bottom,
                label=t,
                color={
                    "Acts": "tab:blue",
                    "Bills": "tab:orange",
                    "Extraordinary Gazettes": "tab:green",
                    "Gazettes": "tab:red",
                }.get(t, "gray"),
            )
            bottom = [b + c for b, c in zip(bottom, type_to_counts[t])]

    def stat_sig_analysis(self):

        from scipy.stats import chisquare

        doc_type_to_x_to_n = {}
        for x, type_to_n in self.x_to_type_to_n.items():
            for doc_type, n in type_to_n.items():
                if doc_type not in doc_type_to_x_to_n:
                    doc_type_to_x_to_n[doc_type] = {}
                doc_type_to_x_to_n[doc_type][x] = n

        lines = []
        for doc_type, x_to_n in doc_type_to_x_to_n.items():
            values = list(x_to_n.values())

            _, p = chisquare(values)
            decision = (
                "❌ No statistically significant"
                if p >= 0.05
                else "✅ Statistically significant"
            )

            lines.append(
                f"{decision} (p-value={p:.3f})"
                + f" difference in **{doc_type}**"
            )
            lines.append("")

        return lines + [""]

    def draw_chart(self):

        dates, all_types, type_to_counts = self.__build_data__()

        _, ax = plt.subplots(figsize=(8, 4.5))
        self.draw_stacked_bar_chart(ax, dates, all_types, type_to_counts)

        n = len(self.doc_list)
        ax.set_title(f"Document Count by {self.t_label.title()} ({n=:,})")
        ax.legend(title="Document Type")

        shown_ticks = self.get_show_ticks(dates)
        ax.set_xticks(shown_ticks)
        ax.set_xticklabels(shown_ticks, ha="center")

        plt.tight_layout()

        dir_images = "images"
        os.makedirs(dir_images, exist_ok=True)
        image_path = os.path.join(
            dir_images, f"chart-document-count-by-{self.t_label}.png"
        )
        plt.savefig(image_path, dpi=300)
        plt.close()
        log.info(f"Wrote {image_path}.")
        return image_path, self.stat_sig_analysis()
