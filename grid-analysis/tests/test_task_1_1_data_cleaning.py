"""
Tests for Task 1.1 (data cleaning and preprocessing - OOP version).

Two layers:
  - Unit tests against tiny synthetic DataFrames, instantiating the task's
    own classes directly - fast, deterministic, and they test the *logic*
    (does it actually catch a bad row?) rather than just "did the seeded
    dataset come out clean" (which it always will, by construction).
  - Integration tests against the real pipeline output (the `pipeline`
    fixture), checking the actual deliverables: the three clean CSVs and
    the report.
"""
import os

import pandas as pd

import task_1_1_data_cleaning as t11


# ---------------------------------------------------------------------------
# Unit tests - synthetic data, exercising the classes directly
# ---------------------------------------------------------------------------
def test_standardize_missing_indicators_replaces_common_spellings():
    df = pd.DataFrame({"Utility ID": [1, 2, 3, 4, 5],
                        "Region": ["Ashanti", "NULL", "", " ", "N/A"]})
    cleaner = t11.SubstationsCleaner(df)
    cleaner.standardize_missing_indicators()
    assert cleaner.df["Region"].isnull().sum() == 4
    assert cleaner.df["Region"].iloc[0] == "Ashanti"


def test_enforce_dtypes_coerces_valid_numeric_column():
    df = pd.DataFrame({
        "Substation ID": [1, 2, 3], "Latitude": ["5.6", "6.1", "7.3"],
        "Longitude": [0.0, 0.0, 0.0], "Voltage (kV)": [11, 11, 11],
        "Capacity (MVA)": [10.0, 10.0, 10.0], "Commissioning Year": [2000, 2000, 2000],
    })
    cleaner = t11.SubstationsCleaner(df)
    cleaner.enforce_dtypes()
    assert cleaner.df["Latitude"].dtype.kind == "f"
    assert cleaner.dtype_coercion_issues == {}


def test_enforce_dtypes_coerces_id_columns_too():
    """Regression test: enforce_dtypes must also coerce ID/FK columns, not
    just the continuous measurement columns - otherwise a stringified ID
    column silently breaks the isin()-based relationship checks later."""
    df = pd.DataFrame({
        "Substation ID": [1, 2, "not-a-number"],
        "Latitude": [5.0, 6.0, 7.0], "Longitude": [0.0, 0.0, 0.0],
        "Voltage (kV)": [11, 11, 11], "Capacity (MVA)": [10.0, 10.0, 10.0],
        "Commissioning Year": [2000, 2000, 2000],
    })
    cleaner = t11.SubstationsCleaner(df)
    cleaner.enforce_dtypes()
    assert cleaner.df["Substation ID"].isnull().sum() == 1
    assert cleaner.dtype_coercion_issues.get("Substation ID") == 1


def test_drop_rows_missing_key_drops_null_ids_only():
    df = pd.DataFrame({"Utility ID": [1, None, 3], "Name": ["A", "B", "C"]})
    cleaner = t11.UtilitiesCleaner(df)
    cleaner.drop_rows_missing_key()
    assert cleaner.dropped_missing_key == 1
    assert len(cleaner.df) == 2
    assert cleaner.df["Utility ID"].tolist() == [1, 3]


def test_find_duplicate_keys_detects_duplicates():
    df = pd.DataFrame({"Substation ID": [1, 2, 2, 3], "Name": ["A", "B", "B-dup", "C"]})
    cleaner = t11.SubstationsCleaner(df)
    cleaner.find_duplicate_keys()
    assert set(cleaner.duplicate_key_ids) == {2}
    assert cleaner.duplicate_key_ids.count(2) == 2  # both rows sharing the duplicated key


def test_check_coordinate_bounds_flags_outliers():
    df = pd.DataFrame({
        "Substation ID": [1, 2, 3],
        "Name": ["In Bounds", "Bad Latitude", "Bad Longitude"],
        "Latitude": [6.0, 90.0, 6.0],
        "Longitude": [-1.0, -1.0, 200.0],
    })
    cleaner = t11.SubstationsCleaner(df)
    out_of_bounds = cleaner.check_coordinate_bounds()
    assert set(out_of_bounds["Substation ID"]) == {2, 3}


def test_impute_categoricals_fills_with_unknown_not_dropped():
    df = pd.DataFrame({"Substation ID": [1, 2], "Region": ["Ashanti", None]})
    cleaner = t11.SubstationsCleaner(df)
    cleaner.impute_categoricals()
    assert len(cleaner.df) == 2  # row survives
    assert cleaner.df["Region"].iloc[1] == "Unknown"


def test_clean_runs_full_pipeline_in_order():
    """The clean() template method should standardise, coerce, drop missing
    keys, and impute - end to end - for a single call."""
    df = pd.DataFrame({
        "Substation ID": [1, 2, None], "Name": ["A", "B", "C"],
        "Region": ["Ashanti", "NULL", "Volta"], "Type": ["Distribution"] * 3,
        "Status": ["Active"] * 3, "Country": ["Ghana"] * 3,
        "Latitude": [6.0, 6.1, 6.2], "Longitude": [-1.0, -1.1, -1.2],
        "Voltage (kV)": [11, 11, 11], "Capacity (MVA)": [10.0, 10.0, 10.0],
        "Commissioning Year": [2000, 2000, 2000],
    })
    cleaner = t11.SubstationsCleaner(df)
    cleaned = cleaner.clean()
    assert len(cleaned) == 2  # the row with a missing Substation ID is dropped
    assert cleaner.dropped_missing_key == 1
    assert cleaned["Region"].iloc[1] == "Unknown"  # "NULL" -> NaN -> "Unknown"


def test_relationship_validator_detects_orphaned_source_and_utility():
    utilities = pd.DataFrame({"Utility ID": [1, 2]})
    substations = pd.DataFrame({"Substation ID": [10, 20]})
    lines = pd.DataFrame({
        "Line ID": [100, 101, 102],
        "Source Substation ID": [10, 999, 10],       # 999 doesn't exist
        "Destination Substation ID": [20, 20, 20],
        "Utility ID": [1, 1, 5],                       # 5 doesn't exist
    })
    result = t11.RelationshipValidator(utilities, substations, lines).validate()
    assert result["orphaned_source_line_ids"] == [101]
    assert result["orphaned_destination_line_ids"] == []
    assert result["orphaned_utility_line_ids"] == [102]


def test_relationship_validator_passes_for_consistent_data():
    utilities = pd.DataFrame({"Utility ID": [1]})
    substations = pd.DataFrame({"Substation ID": [10, 20]})
    lines = pd.DataFrame({
        "Line ID": [100], "Source Substation ID": [10],
        "Destination Substation ID": [20], "Utility ID": [1],
    })
    result = t11.RelationshipValidator(utilities, substations, lines).validate()
    assert result["orphaned_source_line_ids"] == []
    assert result["orphaned_destination_line_ids"] == []
    assert result["orphaned_utility_line_ids"] == []


# ---------------------------------------------------------------------------
# Integration tests - real pipeline output
# ---------------------------------------------------------------------------
def test_cleaned_csvs_exist_with_expected_row_counts(pipeline):
    utilities = pd.read_csv(os.path.join(pipeline["clean"], "utilities_clean.csv"))
    substations = pd.read_csv(os.path.join(pipeline["clean"], "substations_clean.csv"))
    lines = pd.read_csv(os.path.join(pipeline["clean"], "lines_clean.csv"))
    # Matches the seeded generator's documented output exactly.
    assert len(utilities) == 10
    assert len(substations) == 44
    assert len(lines) == 55


def test_cleaned_substations_have_no_duplicate_ids(pipeline):
    substations = pd.read_csv(os.path.join(pipeline["clean"], "substations_clean.csv"))
    assert substations["Substation ID"].is_unique


def test_cleaned_lines_have_no_dangling_foreign_keys(pipeline):
    substations = pd.read_csv(os.path.join(pipeline["clean"], "substations_clean.csv"))
    lines = pd.read_csv(os.path.join(pipeline["clean"], "lines_clean.csv"))
    valid_ids = set(substations["Substation ID"])
    assert set(lines["Source Substation ID"]).issubset(valid_ids)
    assert set(lines["Destination Substation ID"]).issubset(valid_ids)


def test_cleaned_substation_coordinates_within_bounds(pipeline):
    substations = pd.read_csv(os.path.join(pipeline["clean"], "substations_clean.csv"))
    assert substations["Latitude"].between(*t11.SubstationsCleaner.LAT_BOUNDS).all()
    assert substations["Longitude"].between(*t11.SubstationsCleaner.LON_BOUNDS).all()


def test_cleaned_csvs_have_no_missing_values(pipeline):
    for name in ("utilities", "substations", "lines"):
        df = pd.read_csv(os.path.join(pipeline["clean"], f"{name}_clean.csv"))
        assert df.isnull().sum().sum() == 0, f"{name}_clean.csv has unexpected missing values"


def test_report_documents_zero_issues_on_the_seeded_dataset(pipeline):
    report_path = os.path.join(pipeline["reports"], "task_1_1_data_cleaning_report.md")
    assert os.path.exists(report_path)
    with open(report_path) as f:
        content = f.read()
    assert "Duplicate Substation IDs:** none found" in content
    assert "orphaned Source Substation ID:** none found" in content
    assert "orphaned Utility ID:** none found" in content


def test_pipeline_run_returns_a_cleaner_per_table(pipeline):
    """DataCleaningPipeline.run() should hand back one cleaner instance per
    table, each still carrying its recorded validation state."""
    result = t11.DataCleaningPipeline().run()
    assert set(result.keys()) == {"utilities", "substations", "lines"}
    assert isinstance(result["substations"], t11.SubstationsCleaner)
    assert result["substations"].dropped_missing_key == 0


def test_rerunning_task_1_1_is_reproducible(pipeline, run_pipeline_script):
    """Re-run the script a second time and confirm byte-identical CSV output -
    this is the reproducibility check the spec explicitly asks for."""
    path = os.path.join(pipeline["clean"], "substations_clean.csv")
    with open(path, "rb") as f:
        before = f.read()

    run_pipeline_script(os.path.join("tasks", "task_1_1_data_cleaning.py"))

    with open(path, "rb") as f:
        after = f.read()
    assert before == after
