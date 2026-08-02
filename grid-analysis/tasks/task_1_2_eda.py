"""
Task 1.2: Exploratory Data Analysis (Team Member 2 - Data Analyst)

Objective: understand dataset characteristics and identify initial patterns in
the cleaned grid dataset (Task 1.1's output), producing:

    1. A comprehensive EDA report with visualisations
       -> reports/task_1_2_eda_report.md, reports/figures/task_1_2/*.png
    2. Summary statistics tables                        -> included in the report
    3. Initial hypotheses about network structure        -> included in the report
    4. A list of interesting patterns for further
       investigation                                     -> included in the report

Covers the spec's EDA question list directly: region distribution, voltage-level
distribution, top utilities by line count, capacity distribution, oldest
infrastructure by region, active/under-maintenance line proportions, most-connected
substations, and geographic distribution of high-capacity substations.

Run from the grid-analysis/ directory after task_1_1_data_cleaning.py:
    python tasks/task_1_2_eda.py
"""
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless-safe backend - no display required to save PNGs
import matplotlib.pyplot as plt
import pandas as pd

from report_utils import dataframe_to_markdown_table

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures", "task_1_2")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "task_1_2_eda_report.md")

SUBSTATION_NUMERIC_COLS = ["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)", "Commissioning Year"]
LINE_NUMERIC_COLS = ["Voltage (kV)", "Length (km)", "Capacity (MVA)"]

TOP_N = 10


def load_clean():
    utilities = pd.read_csv(os.path.join(CLEAN_DIR, "utilities_clean.csv"))
    substations = pd.read_csv(os.path.join(CLEAN_DIR, "substations_clean.csv"))
    lines = pd.read_csv(os.path.join(CLEAN_DIR, "lines_clean.csv"))
    return utilities, substations, lines


# ---------------------------------------------------------------------------
# Computations - one function per EDA question from the spec
# ---------------------------------------------------------------------------
def region_distribution(substations):
    """Which regions have the greatest number of substations?"""
    return substations["Region"].value_counts()


def voltage_distribution(substations):
    """Which voltage levels are most common?"""
    return substations["Voltage (kV)"].value_counts().sort_index()


def top_utilities_by_lines(lines, utilities):
    """Which utility operates the greatest number of lines?"""
    counts = lines["Utility ID"].value_counts()
    utility_lookup = utilities.set_index("Utility ID")["Alias"]
    result = counts.rename("Line Count").to_frame()
    result["Utility"] = result.index.map(utility_lookup)
    return result[["Utility", "Line Count"]].sort_values("Line Count", ascending=False)


def capacity_distribution(substations):
    """What is the distribution of substation capacities?"""
    return substations["Capacity (MVA)"].describe().round(2)


def oldest_infrastructure_by_region(substations):
    """Which regions contain the oldest infrastructure?"""
    return (substations.groupby("Region")["Commissioning Year"]
            .agg(["mean", "min", "max", "count"]).round(1)
            .sort_values("mean"))


def line_status_proportions(lines):
    """What proportion of lines are active or under maintenance?"""
    counts = lines["Status"].value_counts()
    proportions = (counts / counts.sum() * 100).round(1)
    result = pd.DataFrame({"Count": counts, "Percent": proportions})
    return result


def most_connected_substations(lines, substations, top_n=TOP_N):
    """Which substations have the greatest number of connections?"""
    degree = pd.concat([
        lines["Source Substation"].value_counts(),
        lines["Destination Substation"].value_counts(),
    ], axis=1).fillna(0)
    degree.columns = ["as_source", "as_destination"]
    degree["Connections"] = (degree["as_source"] + degree["as_destination"]).astype(int)
    degree = degree.sort_values("Connections", ascending=False).head(top_n)
    # "Source Substation"/"Destination Substation" in lines.csv store the full
    # Name field (e.g. "Achimota Substation"), not the Short Name column.
    region_lookup = substations.set_index("Name")["Region"]
    degree["Region"] = degree.index.map(region_lookup)
    return degree[["Connections", "Region"]]


def high_capacity_substations_by_region(substations, top_n=TOP_N):
    """How are high-capacity substations distributed geographically?"""
    top = substations.sort_values("Capacity (MVA)", ascending=False).head(top_n)
    return top[["Short Name", "Region", "Capacity (MVA)", "Voltage (kV)"]].reset_index(drop=True)


def status_distribution(substations):
    return substations["Status"].value_counts()


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def save_bar_chart(series, title, xlabel, ylabel, filename, rotation=45):
    plt.figure(figsize=(9, 5))
    series.plot(kind="bar", color="#2f6f9f")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotation, ha="right")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, filename)
    plt.savefig(path)
    plt.close()
    return os.path.relpath(path, os.path.dirname(REPORT_PATH)).replace(os.sep, "/")


def save_histogram(series, title, xlabel, filename, bins=10):
    plt.figure(figsize=(9, 5))
    series.dropna().plot(kind="hist", bins=bins, color="#2f6f9f", edgecolor="white")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, filename)
    plt.savefig(path)
    plt.close()
    return os.path.relpath(path, os.path.dirname(REPORT_PATH)).replace(os.sep, "/")


def generate_charts(substations, lines, utilities):
    os.makedirs(FIG_DIR, exist_ok=True)
    figures = {}

    figures["regions"] = save_bar_chart(
        region_distribution(substations), "Substations by Region", "Region",
        "Number of Substations", "eda_regions.png")

    figures["voltage"] = save_bar_chart(
        voltage_distribution(substations), "Substations by Voltage Level (kV)",
        "Voltage (kV)", "Number of Substations", "eda_voltage_distribution.png", rotation=0)

    top_util = top_utilities_by_lines(lines, utilities).head(TOP_N)
    figures["utilities"] = save_bar_chart(
        top_util.set_index("Utility")["Line Count"], "Top Utilities by Number of Lines Operated",
        "Utility", "Number of Lines", "eda_top_utilities.png", rotation=0)

    figures["connected"] = save_bar_chart(
        most_connected_substations(lines, substations)["Connections"],
        f"Top {TOP_N} Most-Connected Substations", "Substation", "Number of Connections",
        "eda_top_connected_substations.png")

    figures["status"] = save_bar_chart(
        status_distribution(substations), "Substation Status", "Status",
        "Number of Substations", "eda_status_distribution.png", rotation=0)

    figures["line_status"] = save_bar_chart(
        lines["Status"].value_counts(), "Line Status", "Status", "Number of Lines",
        "eda_line_status_distribution.png", rotation=0)

    figures["capacity_hist"] = save_histogram(
        substations["Capacity (MVA)"], "Distribution of Substation Capacities",
        "Capacity (MVA)", "eda_capacity_histogram.png")

    figures["age_hist"] = save_histogram(
        substations["Commissioning Year"], "Distribution of Substation Commissioning Years",
        "Commissioning Year", "eda_commissioning_year_histogram.png")

    return figures


# ---------------------------------------------------------------------------
# Hypotheses / patterns (derived from the actual computed results)
# ---------------------------------------------------------------------------
def generate_hypotheses(region_counts, top_util, connected, oldest_by_region, line_status):
    top_region = region_counts.idxmax()
    top_utility_row = top_util.iloc[0]
    top_hub = connected.index[0]
    oldest_region = oldest_by_region["mean"].idxmin()
    newest_region = oldest_by_region["mean"].idxmax()
    maintenance_pct = line_status.loc["Under Maintenance", "Percent"] if "Under Maintenance" in line_status.index else 0

    return [
        f"**{top_region}** has the greatest number of substations "
        f"({int(region_counts.max())}), suggesting it is the network's primary "
        "load centre - consistent with it typically covering the capital/major "
        "urban area in this kind of dataset.",

        f"**{top_utility_row['Utility']}** operates the most lines "
        f"({int(top_utility_row['Line Count'])}), which may reflect either broad "
        "geographic coverage or a transmission-utility role rather than a "
        "distribution-utility role - worth cross-checking against the 'Type' "
        "column in utilities.csv in Task 1.3.",

        f"**{top_hub}** is the most-connected substation in the network "
        f"({int(connected.iloc[0]['Connections'])} connections). A node with this "
        "many connections is a structural hub candidate; Task 2.1's betweenness- "
        "centrality calculation should confirm whether it is also a critical "
        "inter-regional bridge or 'merely' a well-meshed local hub.",

        f"**{oldest_region}** has the oldest average infrastructure "
        f"(mean commissioning year {oldest_by_region.loc[oldest_region, 'mean']}), "
        f"while **{newest_region}** has the newest "
        f"(mean {oldest_by_region.loc[newest_region, 'mean']}). Older assets are a "
        "reasonable proxy for elevated fault risk and should be cross-referenced "
        "against maintenance status in Task 2.3.",

        f"**{maintenance_pct}%** of lines are currently 'Under Maintenance'. If this "
        "proportion is concentrated in a small number of regions or utilities "
        "rather than spread evenly, that concentration itself is worth flagging "
        "as an operational risk indicator.",
    ]


def generate_patterns_for_investigation():
    return [
        "Does substation degree (connection count) correlate with capacity (MVA), "
        "or are some high-degree substations low-capacity 'wiring hubs' rather than "
        "genuine bulk-supply points? Investigate in Task 2.1/2.3.",
        "Do high-capacity substations cluster geographically (e.g. along the coast "
        "or around Accra/Kumasi), or are they evenly spread? Investigate with the "
        "geospatial analysis in Task 2.2.",
        "Is there a relationship between a substation's voltage tier and its "
        "commissioning year (i.e. are higher-voltage transmission assets newer or "
        "older than lower-voltage distribution assets)?",
        "Are cross-border WAPP interconnection substations structurally more "
        "central (higher betweenness) than domestic hubs, given they sit between "
        "otherwise separate national sub-networks?",
        "Does line length correlate with line capacity or voltage - i.e. are "
        "longer lines built to a consistently higher spec, or does the dataset "
        "show under-provisioned long-haul lines worth flagging as upgrade "
        "candidates in Task 2.3?",
    ]


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------
def write_report(utilities, substations, lines):
    figures = generate_charts(substations, lines, utilities)

    region_counts = region_distribution(substations)
    voltage_counts = voltage_distribution(substations)
    top_util = top_utilities_by_lines(lines, utilities)
    capacity_stats = capacity_distribution(substations)
    oldest_by_region = oldest_infrastructure_by_region(substations)
    line_status = line_status_proportions(lines)
    connected = most_connected_substations(lines, substations)
    high_capacity = high_capacity_substations_by_region(substations)
    status_counts = status_distribution(substations)

    numeric_summary_sub = substations[SUBSTATION_NUMERIC_COLS].describe().round(2)
    numeric_summary_lines = lines[LINE_NUMERIC_COLS].describe().round(2)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    out = []
    out.append("# Task 1.2 - Exploratory Data Analysis Report\n")
    out.append(f"_Generated {datetime.now().isoformat(timespec='seconds')}_\n")
    out.append("_Source: `data/cleaned/*.csv` (Task 1.1 output)._\n")

    out.append("\n## 1. Descriptive statistics for numerical variables\n")
    out.append("### Substations\n")
    out.append(dataframe_to_markdown_table(numeric_summary_sub, index_label="stat"))
    out.append("\n\n### Lines\n")
    out.append(dataframe_to_markdown_table(numeric_summary_lines, index_label="stat"))

    out.append("\n\n## 2. Frequency distributions for categorical variables\n")
    out.append("### Substations by Region\n")
    out.append(dataframe_to_markdown_table(region_counts.to_frame("Count"), index_label="Region"))
    out.append(f"\n\n![Substations by region]({figures['regions']})\n")
    out.append("\n### Substations by Voltage Level (kV)\n")
    out.append(dataframe_to_markdown_table(voltage_counts.to_frame("Count"), index_label="Voltage (kV)"))
    out.append(f"\n\n![Voltage distribution]({figures['voltage']})\n")
    out.append("\n### Substation Status\n")
    out.append(dataframe_to_markdown_table(status_counts.to_frame("Count"), index_label="Status"))
    out.append(f"\n\n![Substation status]({figures['status']})\n")
    out.append("\n### Line Status (Active / Under Maintenance)\n")
    out.append(dataframe_to_markdown_table(line_status, index_label="Status"))
    out.append(f"\n\n![Line status]({figures['line_status']})\n")

    out.append("\n\n## 3. Top utilities by number of lines operated\n")
    out.append(dataframe_to_markdown_table(top_util.reset_index(drop=True), index_label="rank"))
    out.append(f"\n\n![Top utilities]({figures['utilities']})\n")

    out.append("\n\n## 4. Most-connected substations\n")
    out.append(dataframe_to_markdown_table(connected, index_label="Substation"))
    out.append(f"\n\n![Most-connected substations]({figures['connected']})\n")

    out.append("\n\n## 5. Substation capacity distribution\n")
    out.append(dataframe_to_markdown_table(capacity_stats.to_frame("Capacity (MVA)"), index_label="stat"))
    out.append(f"\n\n![Capacity histogram]({figures['capacity_hist']})\n")
    out.append("\n### Highest-capacity substations and their region\n")
    out.append(dataframe_to_markdown_table(high_capacity, index_label="rank"))

    out.append("\n\n## 6. Infrastructure age by region\n")
    out.append(dataframe_to_markdown_table(oldest_by_region, index_label="Region"))
    out.append(f"\n\n![Commissioning year histogram]({figures['age_hist']})\n")

    out.append("\n\n## 7. Initial hypotheses about network structure\n")
    for hypothesis in generate_hypotheses(region_counts, top_util, connected, oldest_by_region, line_status):
        out.append(f"- {hypothesis}\n")

    out.append("\n## 8. Patterns for further investigation\n")
    for pattern in generate_patterns_for_investigation():
        out.append(f"- {pattern}\n")

    out.append("\n## 9. Figures\n")
    for fig_path in figures.values():
        out.append(f"- `{fig_path}`\n")

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(out))


def main():
    utilities, substations, lines = load_clean()
    write_report(utilities, substations, lines)
    print("Task 1.2 complete.")
    print(f"  Report written to reports/task_1_2_eda_report.md")
    print(f"  Figures written to reports/figures/task_1_2/")


if __name__ == "__main__":
    main()
