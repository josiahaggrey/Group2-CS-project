"""Tests for Task 1.3 (data integration and relationship mapping)."""
import json
import os

import pandas as pd

import task_1_3_data_integration as t13


def make_utilities():
    return pd.DataFrame({
        "Utility ID": [1, 2], "Name": ["Utility One", "Utility Two"],
        "Alias": ["U1", "U2"], "Code": ["ONE", "TWO"], "Type": ["Distribution", "Transmission"],
        "Country": ["Ghana", "Ghana"], "Active": ["Y", "Y"],
    })


def make_substations():
    return pd.DataFrame({
        "Substation ID": [10, 20, 30], "Name": ["Alpha", "Beta", "Gamma"],
        "Short Name": ["A", "B", "C"], "Region": ["R1", "R1", "R2"], "Country": ["Ghana"] * 3,
        "Latitude": [6.0, 6.1, 6.2], "Longitude": [-1.0, -1.1, -1.2],
        "Voltage (kV)": [11, 33, 69], "Capacity (MVA)": [10.0, 20.0, 30.0],
        "Commissioning Year": [2000, 2005, 2010], "Type": ["Distribution"] * 3,
        "Status": ["Active"] * 3,
    })


def make_lines(with_orphan=False):
    rows = {
        "Line ID": [1, 2], "Utility ID": [1, 2],
        "Source Substation ID": [10, 20], "Source Substation": ["Alpha", "Beta"],
        "Destination Substation ID": [20, 30], "Destination Substation": ["Beta", "Gamma"],
        "Voltage (kV)": [11, 33], "Length (km)": [5.0, 8.0], "Capacity (MVA)": [15.0, 25.0],
        "Status": ["Active", "Active"], "Line Type": ["Overhead", "Overhead"],
    }
    if with_orphan:
        rows["Line ID"].append(3)
        rows["Utility ID"].append(1)
        rows["Source Substation ID"].append(9999)  # doesn't exist
        rows["Source Substation"].append("Nowhere")
        rows["Destination Substation ID"].append(30)
        rows["Destination Substation"].append("Gamma")
        rows["Voltage (kV)"].append(11)
        rows["Length (km)"].append(1.0)
        rows["Capacity (MVA)"].append(5.0)
        rows["Status"].append("Active")
        rows["Line Type"].append("Overhead")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Unit tests - synthetic data
# ---------------------------------------------------------------------------
def test_find_and_handle_orphans_drops_only_the_orphan():
    utilities, substations = make_utilities(), make_substations()
    lines = make_lines(with_orphan=True)
    clean_lines, report = t13.find_and_handle_orphans(utilities, substations, lines)
    assert report["orphaned_count"] == 1
    assert report["orphaned_line_ids"] == [3]
    assert len(clean_lines) == 2
    assert 3 not in clean_lines["Line ID"].tolist()


def test_find_and_handle_orphans_keeps_everything_when_consistent():
    utilities, substations = make_utilities(), make_substations()
    lines = make_lines(with_orphan=False)
    clean_lines, report = t13.find_and_handle_orphans(utilities, substations, lines)
    assert report["orphaned_count"] == 0
    assert len(clean_lines) == len(lines)


def test_build_master_dataset_preserves_row_count_and_widens_columns():
    utilities, substations, lines = make_utilities(), make_substations(), make_lines()
    master = t13.build_master_dataset(utilities, substations, lines)
    assert len(master) == len(lines)
    for expected_col in ("Source Region", "Destination Region", "Utility Alias"):
        assert expected_col in master.columns


def test_build_master_dataset_joins_correct_values():
    utilities, substations, lines = make_utilities(), make_substations(), make_lines()
    master = t13.build_master_dataset(utilities, substations, lines)
    row = master[master["Line ID"] == 1].iloc[0]
    assert row["Source Name"] == "Alpha"
    assert row["Source Region"] == "R1"
    assert row["Destination Name"] == "Beta"
    assert row["Utility Alias"] == "U1"


def test_validate_join_passes_for_clean_merge():
    utilities, substations, lines = make_utilities(), make_substations(), make_lines()
    master = t13.build_master_dataset(utilities, substations, lines)
    issues = t13.validate_join(lines, master)
    assert issues == []


def test_build_substation_lookup_returns_native_json_serializable_types():
    substations = make_substations()
    lookup = t13.build_substation_lookup(substations)
    assert 10 in lookup
    entry = lookup[10]
    assert entry["name"] == "Alpha"
    assert isinstance(entry["voltage_kv"], int)
    assert isinstance(entry["capacity_mva"], float)
    # Must round-trip through json.dumps without a custom encoder/default.
    json.dumps(lookup)


def test_build_utility_lookup_keys_by_int_utility_id():
    lookup = t13.build_utility_lookup(make_utilities())
    assert set(lookup.keys()) == {1, 2}
    assert lookup[1]["alias"] == "U1"


# ---------------------------------------------------------------------------
# Integration tests - real pipeline output
# ---------------------------------------------------------------------------
def test_master_dataset_row_count_matches_cleaned_lines(pipeline):
    lines = pd.read_csv(os.path.join(pipeline["clean"], "lines_clean.csv"))
    master = pd.read_csv(os.path.join(pipeline["integrated"], "master_dataset.csv"))
    # No orphans in the seeded dataset, so nothing should be dropped.
    assert len(master) == len(lines)


def test_master_dataset_has_no_null_joins(pipeline):
    master = pd.read_csv(os.path.join(pipeline["integrated"], "master_dataset.csv"))
    assert master["Source Name"].isnull().sum() == 0
    assert master["Destination Name"].isnull().sum() == 0
    assert master["Utility Name"].isnull().sum() == 0


def test_lookup_json_files_are_valid_and_complete(pipeline):
    substations = pd.read_csv(os.path.join(pipeline["clean"], "substations_clean.csv"))
    utilities = pd.read_csv(os.path.join(pipeline["clean"], "utilities_clean.csv"))

    with open(os.path.join(pipeline["integrated"], "substations_lookup.json")) as f:
        sub_lookup = json.load(f)
    with open(os.path.join(pipeline["integrated"], "utilities_lookup.json")) as f:
        util_lookup = json.load(f)

    assert len(sub_lookup) == len(substations)
    assert len(util_lookup) == len(utilities)
    # JSON object keys are always strings - confirm every Substation ID round-trips.
    assert set(sub_lookup.keys()) == {str(i) for i in substations["Substation ID"]}


def test_lookup_values_are_numbers_not_stringified_numbers(pipeline):
    """Regression test for the to_dict() vs iterrows() fragility fix."""
    with open(os.path.join(pipeline["integrated"], "substations_lookup.json")) as f:
        sub_lookup = json.load(f)
    sample = next(iter(sub_lookup.values()))
    assert isinstance(sample["voltage_kv"], int)
    assert isinstance(sample["capacity_mva"], float)
    assert isinstance(sample["commissioning_year"], int)


def test_erd_and_data_dictionary_docs_exist():
    docs_dir = os.path.join(t13.BASE_DIR, "docs")
    assert os.path.exists(os.path.join(docs_dir, "entity_relationship_diagram.md"))
    assert os.path.exists(os.path.join(docs_dir, "data_dictionary.md"))
