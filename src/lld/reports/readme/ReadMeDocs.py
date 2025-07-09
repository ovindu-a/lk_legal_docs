import os

from utils_future import Lang


class ReadMeDocs:
    @staticmethod
    def get_doc_md(doc):
        return (
            f"- {doc.get_emoji()}"
            + f" [{doc.date}]"
            + f" [{doc.description}]({doc.remote_data_url})"
        )

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
                data=ReadMeDocs.get_data(doc),
            )
            d_list.append(d)
        return d_list

    @staticmethod
    def __get_lines_for_docs__(title, doc_list, n_sample=None):
        n = len(doc_list)
        n_sample = n_sample or n
        sampled_doc_list = (
            ReadMeDocs.__sample__(doc_list, n_sample)
            if n > n_sample
            else doc_list
        )

        footer_lines = [""]
        if n > n_sample:
            count_line = f"*(Uniformly Spaced Sample of {
    n_sample:,} from {
        n:,})*",
        else:
            count_line = f"*(Total {n:,} Documents)*"
        return (
            [
                title,
                "",
                count_line,
                "",
            ]
            + [ReadMeDocs.get_doc_md(doc) for doc in sampled_doc_list]
            + footer_lines
        )

    def get_lines_for_recent_docs(self):
        delta_days = 7
        recent_doc_list = [
            doc for doc in self.doc_list if doc.age_days <= delta_days
        ]
        return ReadMeDocs.__get_lines_for_docs__(
            "## Recent Documents"
            + f" (Published during the last {delta_days} days)",
            recent_doc_list,
