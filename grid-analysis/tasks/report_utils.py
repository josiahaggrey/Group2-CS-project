"""Shared helpers for building the per-task markdown reports."""


def dataframe_to_markdown_table(df, index_label="index"):
    """Minimal markdown-table formatter.

    Used instead of pandas' DataFrame.to_markdown() so the report scripts don't
    require the optional `tabulate` dependency just for this.
    """
    if df.empty:
        return "_(no data)_"
    header = [index_label] + [str(c) for c in df.columns]
    rows = [[str(idx)] + [str(v) for v in row] for idx, row in df.iterrows()]
    col_widths = [max(len(str(r[i])) for r in ([header] + rows)) for i in range(len(header))]

    def fmt_row(row):
        return "| " + " | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
    return "\n".join([fmt_row(header), separator] + [fmt_row(r) for r in rows])
