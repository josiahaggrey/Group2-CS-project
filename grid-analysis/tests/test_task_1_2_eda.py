"""Tests for Task 1.2 (exploratory data analysis - OOP version)."""
import os

import pandas as pd

import task_1_2_eda as t12


# ---------------------------------------------------------------------------
# Unit tests - synthetic data, exercising GridEDAAnalyzer directly
# ---------------------------------------------------------------------------
def make_substations():
    return pd.DataFrame({
        "Substation ID": [1, 2, 3, 4],
        "Name": ["A Substation", "B Substation", "C Substation", "D Substation"],
        "Short Name": ["A", "B", "C", "D"],
        "Region": ["Ashanti", "Ashanti", "Volta", "Volta"],
        "Country": ["Ghana"] * 4,
        "Latitude": [6.0, 6.1, 6.2, 6.3],
        "Longitude": [-1.0, -1.1, -1.2, -1.3],
        "Voltage (kV)": [11, 33, 33, 161],
        "Capacity (MVA)": [10.0, 20.0, 30.0, 500.0],
        "Commissioning Year": [2000, 1990, 2010, 2020],
        "Type": ["Distribution", "Distribution", "Distribution", "Transmission"],
        "Status": ["Active", "Active", "Inactive", "Active"],
    })


def make_lines():
    return pd.DataFrame({
        "Line ID": [1, 2, 3],
        "Utility ID": [1, 1, 2],
        "Source Substation ID": [1, 2, 3],
        "Source Substation": ["A Substation", "B Substation", "C Substation"],
        "Destination Substation ID": [2, 3, 4],
        "Destination Substation": ["B Substation", "C Substation", "D Substation"],
        "Voltage (kV)": [11, 33, 33],
        "Length (km)": [10.0, 20.0, 30.0],
        "Capacity (MVA)": [50.0, 60.0, 70.0],
        "Status": ["Active", "Active", "Under Maintenance"],
        "Line Type": ["Overhead", "Overhead", "Underground"],
    })


def make_utilities():
    return pd.DataFrame({"Utility ID": [1, 2], "Alias": ["ECG", "GRIDCo"]})


def make_analyzer():
    return t12.GridEDAAnalyzer(make_utilities(), make_substations(), make_lines())


def test_region_distribution_counts_correctly():
    result = make_analyzer().region_distribution()
    assert result.to_dict() == {"Ashanti": 2, "Volta": 2}


def test_voltage_distribution_sorted_by_voltage_not_frequency():
    result = make_analyzer().voltage_distribution()
    assert list(result.index) == [11, 33, 161]  # ascending voltage order
    assert result.loc[33] == 2


def test_top_utilities_by_lines_maps_id_to_alias():
    result = make_analyzer().top_utilities_by_lines()
    top_row = result.iloc[0]
    assert top_row["Utility"] == "ECG"
    assert top_row["Line Count"] == 2


def test_oldest_infrastructure_by_region_sorted_oldest_first():
    result = make_analyzer().oldest_infrastructure_by_region()
    assert result.index[0] == "Ashanti"  # mean (2000+1990)/2=1995 < Volta's (2010+2020)/2=2015


def test_line_status_proportions_sum_to_100():
    result = make_analyzer().line_status_proportions()
    assert abs(result["Percent"].sum() - 100.0) < 0.01
    assert result.loc["Active", "Count"] == 2
    assert result.loc["Under Maintenance", "Count"] == 1


def test_most_connected_substations_counts_source_and_destination():
    result = make_analyzer().most_connected_substations(top_n=4)
    # B Substation: 1x source (line 2) + 1x destination (line 1) = 2
    assert result.loc["B Substation", "Connections"] == 2
    assert result.loc["B Substation", "Region"] == "Ashanti"


def test_high_capacity_substations_by_region_sorted_descending():
    result = make_analyzer().high_capacity_substations_by_region(top_n=2)
    assert result.iloc[0]["Short Name"] == "D"  # 500 MVA, highest
    assert result.iloc[0]["Capacity (MVA)"] == 500.0


def test_status_distribution_counts_active_and_inactive():
    result = make_analyzer().status_distribution()
    assert result.to_dict() == {"Active": 3, "Inactive": 1}


def test_generate_hypotheses_references_actual_top_values():
    hypotheses = make_analyzer().generate_hypotheses()
    assert len(hypotheses) == 5
    assert any("Ashanti" in h or "Volta" in h for h in hypotheses)


def test_generate_patterns_for_investigation_is_non_empty():
    patterns = t12.GridEDAAnalyzer.generate_patterns_for_investigation()
    assert len(patterns) > 0


# ---------------------------------------------------------------------------
# Integration tests - real pipeline output
# ---------------------------------------------------------------------------
def test_report_and_figures_exist(pipeline):
    report_path = os.path.join(pipeline["reports"], "task_1_2_eda_report.md")
    assert os.path.exists(report_path)

    fig_dir = os.path.join(pipeline["reports"], "figures", "task_1_2")
    expected_figures = [
        "eda_regions.png", "eda_voltage_distribution.png", "eda_top_utilities.png",
        "eda_top_connected_substations.png", "eda_status_distribution.png",
        "eda_line_status_distribution.png", "eda_capacity_histogram.png",
        "eda_commissioning_year_histogram.png",
    ]
    for fig in expected_figures:
        fig_path = os.path.join(fig_dir, fig)
        assert os.path.exists(fig_path), f"missing figure: {fig}"
        assert os.path.getsize(fig_path) > 0, f"figure is empty: {fig}"


def test_report_contains_all_required_sections(pipeline):
    report_path = os.path.join(pipeline["reports"], "task_1_2_eda_report.md")
    with open(report_path) as f:
        content = f.read()
    required_sections = [
        "Descriptive statistics for numerical variables",
        "Frequency distributions for categorical variables",
        "Top utilities by number of lines operated",
        "Most-connected substations",
        "Substation capacity distribution",
        "Infrastructure age by region",
        "Initial hypotheses about network structure",
        "Patterns for further investigation",
    ]
    for section in required_sections:
        assert section in content, f"report missing section: {section}"


def test_image_links_use_forward_slashes(pipeline):
    """Regression test: image paths must be web/markdown-portable (forward
    slashes), not raw os.path.relpath() output on Windows (backslashes)."""
    report_path = os.path.join(pipeline["reports"], "task_1_2_eda_report.md")
    with open(report_path) as f:
        content = f.read()
    assert "\\" not in content, "report contains a backslash - likely an unconverted Windows path"


def test_region_lookup_uses_full_name_not_short_name(pipeline):
    """Regression test: 'Source Substation'/'Destination Substation' in
    lines.csv store the full Name field, not Short Name - the most-connected
    table must not show blank/NaN regions because of a wrong join key."""
    report_path = os.path.join(pipeline["reports"], "task_1_2_eda_report.md")
    with open(report_path) as f:
        content = f.read()
    start = content.index("## 4. Most-connected substations")
    end = content.index("## 5.")
    section = content[start:end]
    assert "nan" not in section.lower()


def test_pipeline_run_returns_a_populated_analyzer(pipeline):
    analyzer = t12.EDAPipeline().run()
    assert isinstance(analyzer, t12.GridEDAAnalyzer)
    assert len(analyzer.substations) == 44
