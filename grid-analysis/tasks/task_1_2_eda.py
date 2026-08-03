"""
Task 1.2: Exploratory Data Analysis (Team Member 2 - Data Analyst) - OOP version.

Objective: understand dataset characteristics and identify initial patterns in
the cleaned grid dataset (Task 1.1's output), producing:

    1. A comprehensive EDA report with visualisations
       -> reports/task_1_2_eda_report.md, reports/figures/task_1_2/*.png
    2. Summary statistics tables                        -> included in the report
    3. Initial hypotheses about network structure        -> included in the report
    4. A list of interesting patterns for further
       investigation                                     -> included in the report

Design: GridEDAAnalyzer wraps the three cleaned DataFrames and exposes one
method per EDA question from the spec (region distribution, voltage
distribution, top utilities by line count, most-connected substations, ...).
ChartGenerator only knows how to render/save a bar chart or histogram and
return a report-relative path - it never touches the domain data directly.
EDAReportBuilder composes an analyzer + a chart generator into the markdown
report. EDAPipeline is the orchestrator (the script's entry point).

Run from the grid-analysis/ directory after task_1_1_data_cleaning.py:
    python tasks/task_1_2_eda.py
"""
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless-safe backend - no display required to save PNGs
import matplotlib.pyplot as plt
import pandas as pd

from report_utils import dataframe_to_markdown_table, require_files

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
FIG_DIR = os.path.join(BASE_DIR, "reports", "figures", "task_1_2")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "task_1_2_eda_report.md")


class GridEDAAnalyzer:
    """Wraps the cleaned dataset and answers each EDA question as a method."""

    TOP_N = 10
    SUBSTATION_NUMERIC_COLS = ["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)", "Commissioning Year"]
    LINE_NUMERIC_COLS = ["Voltage (kV)", "Length (km)", "Capacity (MVA)"]

    def __init__(self, utilities, substations, lines):
        self.utilities = utilities
        self.substations = substations
        self.lines = lines

    def numeric_summary(self):
        return (self.substations[self.SUBSTATION_NUMERIC_COLS].describe().round(2),
                self.lines[self.LINE_NUMERIC_COLS].describe().round(2))

    def region_distribution(self):
        """Which regions have the greatest number of substations?"""
        return self.substations["Region"].value_counts()

    def voltage_distribution(self):
        """Which voltage levels are most common?"""
        return self.substations["Voltage (kV)"].value_counts().sort_index()

    def top_utilities_by_lines(self):
        """Which utility operates the greatest number of lines?"""
        counts = self.lines["Utility ID"].value_counts()
        utility_lookup = self.utilities.set_index("Utility ID")["Alias"]
        result = counts.rename("Line Count").to_frame()
        result["Utility"] = result.index.map(utility_lookup)
        return result[["Utility", "Line Count"]].sort_values("Line Count", ascending=False)

    def capacity_distribution(self):
        """What is the distribution of substation capacities?"""
        return self.substations["Capacity (MVA)"].describe().round(2)

    def oldest_infrastructure_by_region(self):
        """Which regions contain the oldest infrastructure?"""
        return (self.substations.groupby("Region")["Commissioning Year"]
                .agg(["mean", "min", "max", "count"]).round(1)
                .sort_values("mean"))

    def line_status_proportions(self):
        """What proportion of lines are active or under maintenance?"""
        counts = self.lines["Status"].value_counts()
        proportions = (counts / counts.sum() * 100).round(1)
        return pd.DataFrame({"Count": counts, "Percent": proportions})

    def most_connected_substations(self, top_n=None):
        """Which substations have the greatest number of connections?"""
        top_n = self.TOP_N if top_n is None else top_n
        degree = pd.concat([
            self.lines["Source Substation"].value_counts(),
            self.lines["Destination Substation"].value_counts(),
        ], axis=1).fillna(0)
        degree.columns = ["as_source", "as_destination"]
        degree["Connections"] = (degree["as_source"] + degree["as_destination"]).astype(int)
        degree = degree.sort_values("Connections", ascending=False).head(top_n)
        # "Source Substation"/"Destination Substation" in lines.csv store the
        # full Name field (e.g. "Achimota Substation"), not Short Name.
        region_lookup = self.substations.set_index("Name")["Region"]
        degree["Region"] = degree.index.map(region_lookup)
        return degree[["Connections", "Region"]]

    def high_capacity_substations_by_region(self, top_n=None):
        """How are high-capacity substations distributed geographically?"""
        top_n = self.TOP_N if top_n is None else top_n
        top = self.substations.sort_values("Capacity (MVA)", ascending=False).head(top_n)
        return top[["Short Name", "Region", "Capacity (MVA)", "Voltage (kV)"]].reset_index(drop=True)

    def status_distribution(self):
        return self.substations["Status"].value_counts()

    def generate_hypotheses(self):
        """Data-driven hypotheses, referencing the actual computed top values."""
        region_counts = self.region_distribution()
        top_util = self.top_utilities_by_lines()
        connected = self.most_connected_substations()
        oldest_by_region = self.oldest_infrastructure_by_region()
        line_status = self.line_status_proportions()

        top_region = region_counts.idxmax()
        top_utility_row = top_util.iloc[0]
        top_hub = connected.index[0]
        oldest_region = oldest_by_region["mean"].idxmin()
        newest_region = oldest_by_region["mean"].idxmax()
        maintenance_pct = (line_status.loc["Under Maintenance", "Percent"]
                            if "Under Maintenance" in line_status.index else 0)

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

    @staticmethod
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


class ChartGenerator:
    """Only knows how to render/save a chart and return a report-relative
    path - it never looks at what the data *means*, only how to plot it."""

    def __init__(self, fig_dir, report_dir):
        self.fig_dir = fig_dir
        self.report_dir = report_dir
        os.makedirs(self.fig_dir, exist_ok=True)

    def _save(self, filename):
        path = os.path.join(self.fig_dir, filename)
        plt.savefig(path)
        plt.close()
        return os.path.relpath(path, self.report_dir).replace(os.sep, "/")

    def bar_chart(self, series, title, xlabel, ylabel, filename, rotation=45):
        plt.figure(figsize=(9, 5))
        series.plot(kind="bar", color="#2f6f9f")
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=rotation, ha="right")
        plt.tight_layout()
        return self._save(filename)

    def histogram(self, series, title, xlabel, filename, bins=10):
        plt.figure(figsize=(9, 5))
        series.dropna().plot(kind="hist", bins=bins, color="#2f6f9f", edgecolor="white")
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel("Frequency")
        plt.tight_layout()
        return self._save(filename)


class EDAReportBuilder:
    """Composes a GridEDAAnalyzer + a ChartGenerator into the markdown report."""

    def __init__(self, analyzer, chart_generator, report_path):
        self.analyzer = analyzer
        self.charts = chart_generator
        self.report_path = report_path
        self._lines = []

    def _write(self, text=""):
        self._lines.append(text)

    def _generate_all_charts(self):
        a = self.analyzer
        figures = {}
        figures["regions"] = self.charts.bar_chart(
            a.region_distribution(), "Substations by Region", "Region",
            "Number of Substations", "eda_regions.png")
        figures["voltage"] = self.charts.bar_chart(
            a.voltage_distribution(), "Substations by Voltage Level (kV)",
            "Voltage (kV)", "Number of Substations", "eda_voltage_distribution.png", rotation=0)
        top_util = a.top_utilities_by_lines().head(a.TOP_N)
        figures["utilities"] = self.charts.bar_chart(
            top_util.set_index("Utility")["Line Count"], "Top Utilities by Number of Lines Operated",
            "Utility", "Number of Lines", "eda_top_utilities.png", rotation=0)
        figures["connected"] = self.charts.bar_chart(
            a.most_connected_substations()["Connections"], f"Top {a.TOP_N} Most-Connected Substations",
            "Substation", "Number of Connections", "eda_top_connected_substations.png")
        figures["status"] = self.charts.bar_chart(
            a.status_distribution(), "Substation Status", "Status",
            "Number of Substations", "eda_status_distribution.png", rotation=0)
        figures["line_status"] = self.charts.bar_chart(
            a.lines["Status"].value_counts(), "Line Status", "Status", "Number of Lines",
            "eda_line_status_distribution.png", rotation=0)
        figures["capacity_hist"] = self.charts.histogram(
            a.substations["Capacity (MVA)"], "Distribution of Substation Capacities",
            "Capacity (MVA)", "eda_capacity_histogram.png")
        figures["age_hist"] = self.charts.histogram(
            a.substations["Commissioning Year"], "Distribution of Substation Commissioning Years",
            "Commissioning Year", "eda_commissioning_year_histogram.png")
        return figures

    def build(self):
        a = self.analyzer
        figures = self._generate_all_charts()

        region_counts = a.region_distribution()
        voltage_counts = a.voltage_distribution()
        top_util = a.top_utilities_by_lines()
        capacity_stats = a.capacity_distribution()
        oldest_by_region = a.oldest_infrastructure_by_region()
        line_status = a.line_status_proportions()
        connected = a.most_connected_substations()
        high_capacity = a.high_capacity_substations_by_region()
        status_counts = a.status_distribution()
        numeric_summary_sub, numeric_summary_lines = a.numeric_summary()

        self._write("# Task 1.2 - Exploratory Data Analysis Report\n")
        self._write(f"_Generated {datetime.now().isoformat(timespec='seconds')}_\n")
        self._write("_Source: `data/cleaned/*.csv` (Task 1.1 output)._\n")

        self._write("\n## 1. Descriptive statistics for numerical variables\n")
        self._write("### Substations\n")
        self._write(dataframe_to_markdown_table(numeric_summary_sub, index_label="stat"))
        self._write("\n\n### Lines\n")
        self._write(dataframe_to_markdown_table(numeric_summary_lines, index_label="stat"))

        self._write("\n\n## 2. Frequency distributions for categorical variables\n")
        self._write("### Substations by Region\n")
        self._write(dataframe_to_markdown_table(region_counts.to_frame("Count"), index_label="Region"))
        self._write(f"\n\n![Substations by region]({figures['regions']})\n")
        self._write("\n### Substations by Voltage Level (kV)\n")
        self._write(dataframe_to_markdown_table(voltage_counts.to_frame("Count"), index_label="Voltage (kV)"))
        self._write(f"\n\n![Voltage distribution]({figures['voltage']})\n")
        self._write("\n### Substation Status\n")
        self._write(dataframe_to_markdown_table(status_counts.to_frame("Count"), index_label="Status"))
        self._write(f"\n\n![Substation status]({figures['status']})\n")
        self._write("\n### Line Status (Active / Under Maintenance)\n")
        self._write(dataframe_to_markdown_table(line_status, index_label="Status"))
        self._write(f"\n\n![Line status]({figures['line_status']})\n")

        self._write("\n\n## 3. Top utilities by number of lines operated\n")
        self._write(dataframe_to_markdown_table(top_util.reset_index(drop=True), index_label="rank"))
        self._write(f"\n\n![Top utilities]({figures['utilities']})\n")

        self._write("\n\n## 4. Most-connected substations\n")
        self._write(dataframe_to_markdown_table(connected, index_label="Substation"))
        self._write(f"\n\n![Most-connected substations]({figures['connected']})\n")

        self._write("\n\n## 5. Substation capacity distribution\n")
        self._write(dataframe_to_markdown_table(capacity_stats.to_frame("Capacity (MVA)"), index_label="stat"))
        self._write(f"\n\n![Capacity histogram]({figures['capacity_hist']})\n")
        self._write("\n### Highest-capacity substations and their region\n")
        self._write(dataframe_to_markdown_table(high_capacity, index_label="rank"))

        self._write("\n\n## 6. Infrastructure age by region\n")
        self._write(dataframe_to_markdown_table(oldest_by_region, index_label="Region"))
        self._write(f"\n\n![Commissioning year histogram]({figures['age_hist']})\n")

        self._write("\n\n## 7. Initial hypotheses about network structure\n")
        for hypothesis in a.generate_hypotheses():
            self._write(f"- {hypothesis}\n")

        self._write("\n## 8. Patterns for further investigation\n")
        for pattern in a.generate_patterns_for_investigation():
            self._write(f"- {pattern}\n")

        self._write("\n## 9. Figures\n")
        for fig_path in figures.values():
            self._write(f"- `{fig_path}`\n")

        return self

    def write(self):
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, "w") as f:
            f.write("\n".join(self._lines))


class EDAPipeline:
    """Task 1.2 orchestrator - the script's entry point."""

    def __init__(self, clean_dir=CLEAN_DIR, fig_dir=FIG_DIR, report_path=REPORT_PATH):
        self.clean_dir = clean_dir
        self.fig_dir = fig_dir
        self.report_path = report_path

    def load_clean(self):
        paths = [os.path.join(self.clean_dir, f"{name}_clean.csv")
                  for name in ("utilities", "substations", "lines")]
        require_files(paths, "Run tasks/task_1_1_data_cleaning.py first "
                              "(from the grid-analysis/ directory).")
        utilities, substations, lines = (pd.read_csv(p) for p in paths)
        return utilities, substations, lines

    def run(self):
        utilities, substations, lines = self.load_clean()
        analyzer = GridEDAAnalyzer(utilities, substations, lines)
        charts = ChartGenerator(self.fig_dir, os.path.dirname(self.report_path))
        EDAReportBuilder(analyzer, charts, self.report_path).build().write()
        return analyzer


def main():
    pipeline = EDAPipeline()
    pipeline.run()
    print("Task 1.2 complete.")
    print("  Report written to reports/task_1_2_eda_report.md")
    print("  Figures written to reports/figures/task_1_2/")


if __name__ == "__main__":
    main()
