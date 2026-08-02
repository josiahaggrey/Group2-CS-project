"""
Task 1.1: Data Cleaning and Preprocessing (All Team Members)

Objective: transform the raw CSV files produced by generate_dataset.py into
clean, validated datasets, and produce the four deliverables the spec asks for:

    1. Three clean CSV files with proper headers      -> data/cleaned/*.csv
    2. A data-cleaning report documenting all
       transformations                                -> reports/task_1_1_data_cleaning_report.md
    3. A basic statistics summary for each dataset     -> included in the report
    4. A data-quality assessment with identified
       issues                                          -> included in the report

Even though the seeded generator produces internally-consistent data, every
check below is treated as a real validation step (not skipped) because a real
utility's asset register can contain incomplete, duplicated, mistyped, or
outdated records - the point of this task is to demonstrate the *method*,
not just to confirm the toy dataset is clean.

Run from the grid-analysis/ directory after generate_dataset.py:
    python tasks/task_1_1_data_cleaning.py
"""
import os
from datetime import datetime

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "task_1_1_data_cleaning_report.md")

# Plausible West African bounding box (covers Ghana plus the WAPP cross-border
# hubs the generator creates in Cote d'Ivoire, Togo, Benin, Burkina Faso, and
# Guinea). Rows outside this box are flagged, not silently dropped.
LAT_BOUNDS = (4.0, 15.0)
LON_BOUNDS = (-18.0, 5.0)

MISSING_VALUE_INDICATORS = ["\\N", "NULL", "null", "", " ", "NA", "N/A"]

NUMERIC_COLUMNS = {
    "utilities": [],
    "substations": ["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)", "Commissioning Year"],
    "lines": ["Voltage (kV)", "Length (km)", "Capacity (MVA)"],
}

# Documented imputation strategy per dataset. Applied even though the seeded
# generator does not currently produce gaps, so the pipeline is ready for a
# messier real-world extract.
IMPUTATION_STRATEGY = {
    "utilities": "Categorical/text fields (Name, Alias, Code, Type, Country, Active): "
                  "no imputation - a missing utility identity is a data-collection defect "
                  "that must be corrected at the source, not guessed. Rows with a missing "
                  "'Utility ID' are dropped as unusable.",
    "substations": "Numeric fields (Latitude, Longitude, Capacity (MVA), Commissioning Year): "
                   "left as NaN and flagged, never imputed - substituting a fabricated "
                   "coordinate or capacity would be actively misleading for network/geospatial "
                   "analysis. Categorical fields (Region, Type, Status): missing values are "
                   "labelled 'Unknown' so the row survives filtering/grouping instead of "
                   "silently vanishing from region-level aggregates.",
    "lines": "Numeric fields (Length (km), Capacity (MVA)): left as NaN and flagged - "
             "length can be recomputed from source/destination coordinates via the "
             "haversine formula where both substations are known, so that is the intended "
             "fallback rather than a blind fill. Status/Line Type: missing values are "
             "labelled 'Unknown' rather than assumed 'Active'/'Overhead', since assuming "
             "the optimistic default would understate risk in reliability analysis.",
}


def load_raw():
    utilities = pd.read_csv(os.path.join(RAW_DIR, "utilities.csv"))
    substations = pd.read_csv(os.path.join(RAW_DIR, "substations.csv"))
    lines = pd.read_csv(os.path.join(RAW_DIR, "lines.csv"))
    return {"utilities": utilities, "substations": substations, "lines": lines}


def inspect(df, name):
    return {
        "name": name,
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_before": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def standardize_missing_indicators(df):
    """Replace common missing-value spellings with a real NaN before anything else."""
    return df.replace(MISSING_VALUE_INDICATORS, np.nan)


def enforce_dtypes(df, name):
    """Coerce declared numeric columns to numeric, tracking values that failed to convert."""
    coercion_issues = {}
    for col in NUMERIC_COLUMNS.get(name, []):
        if col not in df.columns:
            continue
        before_non_null = df[col].notna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_non_null = df[col].notna().sum()
        newly_null = before_non_null - after_non_null
        if newly_null > 0:
            coercion_issues[col] = int(newly_null)
    return df, coercion_issues


def impute_categoricals(df, categorical_cols):
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")
    return df


def drop_rows_missing_key(df, key_col):
    before = len(df)
    df = df.dropna(subset=[key_col])
    dropped = before - len(df)
    return df, dropped


def check_duplicate_keys(df, key_col):
    return df[df.duplicated(subset=[key_col], keep=False)]


def validate_relationships(utilities, substations, lines):
    valid_sub_ids = set(substations["Substation ID"])
    valid_utility_ids = set(utilities["Utility ID"])

    orphaned_source = lines[~lines["Source Substation ID"].isin(valid_sub_ids)]
    orphaned_dest = lines[~lines["Destination Substation ID"].isin(valid_sub_ids)]
    orphaned_utility = lines[~lines["Utility ID"].isin(valid_utility_ids)]

    return {
        "orphaned_source_line_ids": orphaned_source["Line ID"].tolist(),
        "orphaned_destination_line_ids": orphaned_dest["Line ID"].tolist(),
        "orphaned_utility_line_ids": orphaned_utility["Line ID"].tolist(),
    }


def check_coordinate_bounds(substations):
    out_of_bounds = substations[
        ~substations["Latitude"].between(*LAT_BOUNDS)
        | ~substations["Longitude"].between(*LON_BOUNDS)
    ]
    return out_of_bounds[["Substation ID", "Name", "Latitude", "Longitude"]]


def basic_stats_summary(df, name):
    numeric_cols = NUMERIC_COLUMNS.get(name, [])
    numeric_cols = [c for c in numeric_cols if c in df.columns]
    if not numeric_cols:
        return pd.DataFrame()
    return df[numeric_cols].describe().round(2)


def dataframe_to_markdown_table(df):
    """Minimal markdown-table formatter, used instead of DataFrame.to_markdown()
    so the report doesn't pull in the optional `tabulate` dependency."""
    if df.empty:
        return "_(no numeric columns)_"
    header = ["stat"] + list(df.columns)
    rows = [[str(idx)] + [str(v) for v in row] for idx, row in df.iterrows()]
    col_widths = [max(len(str(r[i])) for r in ([header] + rows)) for i in range(len(header))]

    def fmt_row(row):
        return "| " + " | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
    return "\n".join([fmt_row(header), separator] + [fmt_row(r) for r in rows])


def clean_dataset(raw):
    report_sections = {}

    # ---- utilities -----------------------------------------------------
    utilities = standardize_missing_indicators(raw["utilities"].copy())
    utilities, dropped_utilities = drop_rows_missing_key(utilities, "Utility ID")
    utility_dupe_ids = check_duplicate_keys(utilities, "Utility ID")
    utilities = utilities.drop_duplicates()

    # ---- substations -----------------------------------------------------
    substations = standardize_missing_indicators(raw["substations"].copy())
    substations, dtype_issues_sub = enforce_dtypes(substations, "substations")
    substations, dropped_substations = drop_rows_missing_key(substations, "Substation ID")
    substation_dupe_ids = check_duplicate_keys(substations, "Substation ID")
    substations = impute_categoricals(substations, ["Region", "Type", "Status", "Country"])
    out_of_bounds = check_coordinate_bounds(substations)
    substations = substations.drop_duplicates()

    # ---- lines -----------------------------------------------------
    lines = standardize_missing_indicators(raw["lines"].copy())
    lines, dtype_issues_lines = enforce_dtypes(lines, "lines")
    lines, dropped_lines = drop_rows_missing_key(lines, "Line ID")
    line_dupe_ids = check_duplicate_keys(lines, "Line ID")
    lines = impute_categoricals(lines, ["Status", "Line Type"])
    lines = lines.drop_duplicates()

    relationships = validate_relationships(utilities, substations, lines)

    report_sections["dropped_rows"] = {
        "utilities_missing_key": dropped_utilities,
        "substations_missing_key": dropped_substations,
        "lines_missing_key": dropped_lines,
    }
    report_sections["duplicate_keys"] = {
        "utilities": utility_dupe_ids["Utility ID"].tolist(),
        "substations": substation_dupe_ids["Substation ID"].tolist(),
        "lines": line_dupe_ids["Line ID"].tolist(),
    }
    report_sections["dtype_coercion_issues"] = {
        "substations": dtype_issues_sub,
        "lines": dtype_issues_lines,
    }
    report_sections["out_of_bounds_coordinates"] = out_of_bounds.to_dict("records")
    report_sections["relationship_issues"] = relationships

    cleaned = {"utilities": utilities, "substations": substations, "lines": lines}
    return cleaned, report_sections


def write_cleaned_csvs(cleaned):
    os.makedirs(CLEAN_DIR, exist_ok=True)
    for name, df in cleaned.items():
        df.to_csv(os.path.join(CLEAN_DIR, f"{name}_clean.csv"), index=False)


def format_issue_list(label, values):
    if not values:
        return f"- **{label}:** none found.\n"
    return f"- **{label}:** {len(values)} found -> {values}\n"


def write_report(raw_inspections, cleaned, report_sections):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    lines_out = []
    lines_out.append("# Task 1.1 - Data Cleaning and Preprocessing Report\n")
    lines_out.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_\n")

    lines_out.append("## 1. Raw dataset inspection\n")
    for insp in raw_inspections:
        lines_out.append(f"### {insp['name']}\n")
        lines_out.append(f"- Shape: {insp['shape'][0]} rows x {insp['shape'][1]} columns\n")
        lines_out.append(f"- Duplicate rows (raw): {insp['duplicate_rows']}\n")
        missing = {k: v for k, v in insp["missing_before"].items() if v > 0}
        lines_out.append(f"- Columns with missing values (raw): {missing or 'none'}\n")

    lines_out.append("\n## 2. Missing-value handling strategy\n")
    for name, rationale in IMPUTATION_STRATEGY.items():
        lines_out.append(f"- **{name}:** {rationale}\n")

    lines_out.append("\n## 3. Transformations applied\n")
    dropped = report_sections["dropped_rows"]
    lines_out.append(f"- Rows dropped for missing primary key - utilities: "
                      f"{dropped['utilities_missing_key']}, substations: "
                      f"{dropped['substations_missing_key']}, lines: {dropped['lines_missing_key']}\n")
    lines_out.append("- Standardised missing-value spellings "
                      f"({MISSING_VALUE_INDICATORS}) to NaN before any other processing.\n")
    lines_out.append("- Coerced declared numeric columns via pd.to_numeric(errors='coerce') "
                      "and recorded any values that failed to convert.\n")
    lines_out.append("- Filled missing categorical fields (Region/Type/Status/Country/Line Type) "
                      "with 'Unknown' rather than dropping the row.\n")
    lines_out.append("- Removed exact full-row duplicates from each dataset.\n")

    lines_out.append("\n## 4. Data quality assessment\n")
    lines_out.append(format_issue_list(
        "Duplicate Utility IDs", report_sections["duplicate_keys"]["utilities"]))
    lines_out.append(format_issue_list(
        "Duplicate Substation IDs", report_sections["duplicate_keys"]["substations"]))
    lines_out.append(format_issue_list(
        "Duplicate Line IDs", report_sections["duplicate_keys"]["lines"]))
    lines_out.append(format_issue_list(
        "Lines with an orphaned Source Substation ID",
        report_sections["relationship_issues"]["orphaned_source_line_ids"]))
    lines_out.append(format_issue_list(
        "Lines with an orphaned Destination Substation ID",
        report_sections["relationship_issues"]["orphaned_destination_line_ids"]))
    lines_out.append(format_issue_list(
        "Lines with an orphaned Utility ID",
        report_sections["relationship_issues"]["orphaned_utility_line_ids"]))
    lines_out.append(format_issue_list(
        "Substations with coordinates outside the plausible West Africa bounding box "
        f"(lat {LAT_BOUNDS}, lon {LON_BOUNDS})",
        report_sections["out_of_bounds_coordinates"]))
    sub_dtype = report_sections["dtype_coercion_issues"]["substations"]
    line_dtype = report_sections["dtype_coercion_issues"]["lines"]
    lines_out.append(format_issue_list("Substation numeric columns with non-numeric values", sub_dtype))
    lines_out.append(format_issue_list("Line numeric columns with non-numeric values", line_dtype))

    lines_out.append("\n## 5. Basic statistics summary (post-cleaning)\n")
    for name, df in cleaned.items():
        summary = basic_stats_summary(df, name)
        if summary.empty:
            continue
        lines_out.append(f"### {name}\n")
        lines_out.append(dataframe_to_markdown_table(summary))
        lines_out.append("\n")

    lines_out.append("\n## 6. Output\n")
    for name in cleaned:
        lines_out.append(f"- `data/cleaned/{name}_clean.csv`\n")

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines_out))


def main():
    raw = load_raw()
    raw_inspections = [inspect(df, name) for name, df in raw.items()]
    cleaned, report_sections = clean_dataset(raw)
    write_cleaned_csvs(cleaned)
    write_report(raw_inspections, cleaned, report_sections)

    print("Task 1.1 complete.")
    for name, df in cleaned.items():
        print(f"  {name}: {len(df)} clean rows -> data/cleaned/{name}_clean.csv")
    print(f"  Report written to reports/task_1_1_data_cleaning_report.md")


if __name__ == "__main__":
    main()
