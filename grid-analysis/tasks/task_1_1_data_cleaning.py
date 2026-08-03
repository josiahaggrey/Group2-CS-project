"""
Task 1.1: Data Cleaning and Preprocessing (All Team Members) - OOP version.

Objective: transform the raw CSV files produced by generate_dataset.py into
clean, validated datasets, and produce the four deliverables the spec asks for:

    1. Three clean CSV files with proper headers      -> data/cleaned/*.csv
    2. A data-cleaning report documenting all
       transformations                                -> reports/task_1_1_data_cleaning_report.md
    3. A basic statistics summary for each dataset     -> included in the report
    4. A data-quality assessment with identified
       issues                                          -> included in the report

Design: DatasetCleaner is an abstract base class implementing the cleaning
pipeline once (a template method - standardise -> coerce dtypes -> drop rows
missing their key -> find duplicate keys -> impute categoricals -> drop
duplicate rows), with UtilitiesCleaner/SubstationsCleaner/LinesCleaner
subclasses declaring *what* to clean via class attributes rather than
reimplementing *how*. RelationshipValidator, CleaningReportBuilder, and the
DataCleaningPipeline orchestrator are each a separate class with one
responsibility, composed together in DataCleaningPipeline.run().

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

from report_utils import dataframe_to_markdown_table, require_files

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "task_1_1_data_cleaning_report.md")


class DatasetCleaner:
    """Base class for a single table's cleaning pipeline (template method
    pattern). Subclasses only declare configuration via class attributes;
    `clean()` itself never needs to be overridden."""

    name = None
    key_column = None
    numeric_columns = []
    id_columns = []
    categorical_columns = []
    imputation_strategy = ""

    # Common missing-value spellings, standardised to real NaN before
    # anything else runs.
    MISSING_VALUE_INDICATORS = ["\\N", "NULL", "null", "", " ", "NA", "N/A"]

    def __init__(self, raw_df):
        self.df = raw_df.copy()
        self.dropped_missing_key = 0
        self.duplicate_key_ids = []
        self.dtype_coercion_issues = {}

    def standardize_missing_indicators(self):
        self.df = self.df.replace(self.MISSING_VALUE_INDICATORS, np.nan)
        return self

    def enforce_dtypes(self):
        """Coerce declared numeric AND id/foreign-key columns to numeric.
        ID columns matter here too: an ID column that arrived as strings
        (e.g. one stray non-numeric value forcing object dtype for the whole
        column) would otherwise silently break isin()-based relationship
        checks downstream, since comparing int64 substation IDs against
        stringified line IDs never matches."""
        for col in self.numeric_columns + self.id_columns:
            if col not in self.df.columns:
                continue
            before_non_null = self.df[col].notna().sum()
            self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
            after_non_null = self.df[col].notna().sum()
            newly_null = before_non_null - after_non_null
            if newly_null > 0:
                self.dtype_coercion_issues[col] = int(newly_null)
        return self

    def drop_rows_missing_key(self):
        before = len(self.df)
        self.df = self.df.dropna(subset=[self.key_column])
        self.dropped_missing_key = before - len(self.df)
        return self

    def find_duplicate_keys(self):
        dupes = self.df[self.df.duplicated(subset=[self.key_column], keep=False)]
        self.duplicate_key_ids = dupes[self.key_column].tolist()
        return self

    def impute_categoricals(self):
        for col in self.categorical_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna("Unknown")
        return self

    def drop_duplicate_rows(self):
        self.df = self.df.drop_duplicates()
        return self

    def clean(self):
        """Run the full pipeline in order; returns the cleaned DataFrame."""
        (self.standardize_missing_indicators()
             .enforce_dtypes()
             .drop_rows_missing_key()
             .find_duplicate_keys()
             .impute_categoricals()
             .drop_duplicate_rows())
        return self.df

    def basic_stats_summary(self):
        cols = [c for c in self.numeric_columns if c in self.df.columns]
        if not cols:
            return pd.DataFrame()
        return self.df[cols].describe().round(2)


class UtilitiesCleaner(DatasetCleaner):
    name = "utilities"
    key_column = "Utility ID"
    id_columns = ["Utility ID"]
    imputation_strategy = (
        "Categorical/text fields (Name, Alias, Code, Type, Country, Active): "
        "no imputation - a missing utility identity is a data-collection defect "
        "that must be corrected at the source, not guessed. Rows with a missing "
        "'Utility ID' are dropped as unusable."
    )


class SubstationsCleaner(DatasetCleaner):
    name = "substations"
    key_column = "Substation ID"
    numeric_columns = ["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)", "Commissioning Year"]
    id_columns = ["Substation ID"]
    categorical_columns = ["Region", "Type", "Status", "Country"]
    imputation_strategy = (
        "Numeric fields (Latitude, Longitude, Capacity (MVA), Commissioning Year): "
        "left as NaN and flagged, never imputed - substituting a fabricated "
        "coordinate or capacity would be actively misleading for network/geospatial "
        "analysis. Categorical fields (Region, Type, Status): missing values are "
        "labelled 'Unknown' so the row survives filtering/grouping instead of "
        "silently vanishing from region-level aggregates."
    )

    # Plausible West African bounding box (covers Ghana plus the WAPP
    # cross-border hubs the generator creates in Cote d'Ivoire, Togo, Benin,
    # Burkina Faso, and Guinea). Rows outside this box are flagged, not
    # silently dropped.
    LAT_BOUNDS = (4.0, 15.0)
    LON_BOUNDS = (-18.0, 5.0)

    def check_coordinate_bounds(self):
        out_of_bounds = self.df[
            ~self.df["Latitude"].between(*self.LAT_BOUNDS)
            | ~self.df["Longitude"].between(*self.LON_BOUNDS)
        ]
        return out_of_bounds[["Substation ID", "Name", "Latitude", "Longitude"]]


class LinesCleaner(DatasetCleaner):
    name = "lines"
    key_column = "Line ID"
    numeric_columns = ["Voltage (kV)", "Length (km)", "Capacity (MVA)"]
    id_columns = ["Line ID", "Utility ID", "Source Substation ID", "Destination Substation ID"]
    categorical_columns = ["Status", "Line Type"]
    imputation_strategy = (
        "Numeric fields (Length (km), Capacity (MVA)): left as NaN and flagged - "
        "length can be recomputed from source/destination coordinates via the "
        "haversine formula where both substations are known, so that is the intended "
        "fallback rather than a blind fill. Status/Line Type: missing values are "
        "labelled 'Unknown' rather than assumed 'Active'/'Overhead', since assuming "
        "the optimistic default would understate risk in reliability analysis."
    )


class RelationshipValidator:
    """Checks lines' foreign keys (Utility ID, Source/Destination Substation
    ID) against the cleaned reference tables."""

    def __init__(self, utilities_df, substations_df, lines_df):
        self.utilities_df = utilities_df
        self.substations_df = substations_df
        self.lines_df = lines_df

    def validate(self):
        valid_sub_ids = set(self.substations_df["Substation ID"])
        valid_utility_ids = set(self.utilities_df["Utility ID"])

        orphaned_source = self.lines_df[~self.lines_df["Source Substation ID"].isin(valid_sub_ids)]
        orphaned_dest = self.lines_df[~self.lines_df["Destination Substation ID"].isin(valid_sub_ids)]
        orphaned_utility = self.lines_df[~self.lines_df["Utility ID"].isin(valid_utility_ids)]

        return {
            "orphaned_source_line_ids": orphaned_source["Line ID"].tolist(),
            "orphaned_destination_line_ids": orphaned_dest["Line ID"].tolist(),
            "orphaned_utility_line_ids": orphaned_utility["Line ID"].tolist(),
        }


class CleaningReportBuilder:
    """Builds the Task 1.1 markdown report from the cleaners' recorded state."""

    def __init__(self, report_path):
        self.report_path = report_path
        self._lines = []

    def _write(self, text=""):
        self._lines.append(text)

    @staticmethod
    def _format_issue_list(label, values):
        if not values:
            return f"- **{label}:** none found.\n"
        return f"- **{label}:** {len(values)} found -> {values}\n"

    def build(self, raw_inspections, cleaners, relationships, out_of_bounds):
        self._write("# Task 1.1 - Data Cleaning and Preprocessing Report\n")
        self._write(f"_Generated {datetime.now().isoformat(timespec='seconds')}_\n")

        self._write("## 1. Raw dataset inspection\n")
        for insp in raw_inspections:
            self._write(f"### {insp['name']}\n")
            self._write(f"- Shape: {insp['shape'][0]} rows x {insp['shape'][1]} columns\n")
            self._write(f"- Duplicate rows (raw): {insp['duplicate_rows']}\n")
            missing = {k: v for k, v in insp["missing_before"].items() if v > 0}
            self._write(f"- Columns with missing values (raw): {missing or 'none'}\n")

        self._write("\n## 2. Missing-value handling strategy\n")
        for cleaner in cleaners.values():
            self._write(f"- **{cleaner.name}:** {cleaner.imputation_strategy}\n")

        self._write("\n## 3. Transformations applied\n")
        dropped_summary = ", ".join(f"{c.name}: {c.dropped_missing_key}" for c in cleaners.values())
        self._write(f"- Rows dropped for missing primary key - {dropped_summary}\n")
        self._write("- Standardised missing-value spellings "
                     f"({DatasetCleaner.MISSING_VALUE_INDICATORS}) to NaN before any other processing.\n")
        self._write("- Coerced declared numeric/ID columns via pd.to_numeric(errors='coerce') "
                     "and recorded any values that failed to convert.\n")
        self._write("- Filled missing categorical fields with 'Unknown' rather than dropping the row.\n")
        self._write("- Removed exact full-row duplicates from each dataset.\n")

        self._write("\n## 4. Data quality assessment\n")
        for cleaner in cleaners.values():
            self._write(self._format_issue_list(
                f"Duplicate {cleaner.key_column}s", cleaner.duplicate_key_ids))
        self._write(self._format_issue_list(
            "Lines with an orphaned Source Substation ID", relationships["orphaned_source_line_ids"]))
        self._write(self._format_issue_list(
            "Lines with an orphaned Destination Substation ID", relationships["orphaned_destination_line_ids"]))
        self._write(self._format_issue_list(
            "Lines with an orphaned Utility ID", relationships["orphaned_utility_line_ids"]))
        self._write(self._format_issue_list(
            "Substations with coordinates outside the plausible West Africa bounding box "
            f"(lat {SubstationsCleaner.LAT_BOUNDS}, lon {SubstationsCleaner.LON_BOUNDS})",
            out_of_bounds.to_dict("records")))
        for cleaner in cleaners.values():
            self._write(self._format_issue_list(
                f"{cleaner.name.title()} numeric/ID columns with non-numeric values",
                cleaner.dtype_coercion_issues))

        self._write("\n## 5. Basic statistics summary (post-cleaning)\n")
        for cleaner in cleaners.values():
            summary = cleaner.basic_stats_summary()
            if summary.empty:
                continue
            self._write(f"### {cleaner.name}\n")
            self._write(dataframe_to_markdown_table(summary, index_label="stat"))
            self._write("\n")

        self._write("\n## 6. Output\n")
        for cleaner in cleaners.values():
            self._write(f"- `data/cleaned/{cleaner.name}_clean.csv`\n")

        return self

    def write(self):
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, "w") as f:
            f.write("\n".join(self._lines))


class DataCleaningPipeline:
    """Task 1.1 orchestrator - the script's entry point. Composes the
    per-table cleaners, the relationship validator, and the report builder;
    doesn't implement any cleaning logic itself."""

    CLEANER_CLASSES = {
        "utilities": UtilitiesCleaner,
        "substations": SubstationsCleaner,
        "lines": LinesCleaner,
    }

    def __init__(self, raw_dir=RAW_DIR, clean_dir=CLEAN_DIR, report_path=REPORT_PATH):
        self.raw_dir = raw_dir
        self.clean_dir = clean_dir
        self.report_path = report_path
        self.cleaners = {}

    def load_raw(self):
        paths = {name: os.path.join(self.raw_dir, f"{name}.csv") for name in self.CLEANER_CLASSES}
        require_files(paths.values(), "Run generate_dataset.py first (from the grid-analysis/ directory).")
        return {name: pd.read_csv(path) for name, path in paths.items()}

    @staticmethod
    def _inspect(df, name):
        return {
            "name": name,
            "shape": df.shape,
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_before": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
        }

    def run(self):
        raw = self.load_raw()
        raw_inspections = [self._inspect(df, name) for name, df in raw.items()]

        self.cleaners = {
            name: cleaner_cls(raw[name]) for name, cleaner_cls in self.CLEANER_CLASSES.items()
        }
        for cleaner in self.cleaners.values():
            cleaner.clean()

        relationships = RelationshipValidator(
            self.cleaners["utilities"].df, self.cleaners["substations"].df, self.cleaners["lines"].df,
        ).validate()
        out_of_bounds = self.cleaners["substations"].check_coordinate_bounds()

        self._write_cleaned_csvs()
        CleaningReportBuilder(self.report_path).build(
            raw_inspections, self.cleaners, relationships, out_of_bounds).write()

        return self.cleaners

    def _write_cleaned_csvs(self):
        os.makedirs(self.clean_dir, exist_ok=True)
        for name, cleaner in self.cleaners.items():
            cleaner.df.to_csv(os.path.join(self.clean_dir, f"{name}_clean.csv"), index=False)


def main():
    pipeline = DataCleaningPipeline()
    cleaners = pipeline.run()

    print("Task 1.1 complete.")
    for name, cleaner in cleaners.items():
        print(f"  {name}: {len(cleaner.df)} clean rows -> data/cleaned/{name}_clean.csv")
    print("  Report written to reports/task_1_1_data_cleaning_report.md")


if __name__ == "__main__":
    main()
