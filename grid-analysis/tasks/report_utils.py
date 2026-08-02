"""Shared helpers for building the per-task markdown reports."""
import os


def require_files(paths, hint):
    """Fail with a clear, actionable message instead of a raw traceback when an
    earlier pipeline step (e.g. generate_dataset.py or a prior task script)
    hasn't been run yet."""
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        missing_list = "\n".join(f"  - {p}" for p in missing)
        raise FileNotFoundError(f"Missing required input file(s):\n{missing_list}\n\n{hint}")


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
