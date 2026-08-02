"""
Starter analysis script for the National Electricity Grid Network Analysis project.

Run generate_dataset.py first to produce data/utilities.csv, data/substations.csv,
and data/lines.csv. This script walks through the five-task arc from the project
spec: load/inspect, clean, EDA, merge, and network analysis (with an N-1 contingency
check). Split these into a Jupyter notebook per-task as your team develops further.
"""
import os

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data():
    utilities = pd.read_csv(os.path.join(DATA_DIR, "utilities.csv"))
    substations = pd.read_csv(os.path.join(DATA_DIR, "substations.csv"))
    lines = pd.read_csv(os.path.join(DATA_DIR, "lines.csv"))
    return utilities, substations, lines


# ---------------------------------------------------------------------------
# Task 1: Loading and inspecting
# ---------------------------------------------------------------------------
def task1_inspect(utilities, substations, lines):
    print("Utilities DataFrame Info:")
    print(utilities.info(), "\n")
    print("Substations DataFrame Info:")
    print(substations.info(), "\n")
    print("Lines DataFrame Info:")
    print(lines.info(), "\n")


# ---------------------------------------------------------------------------
# Task 2: Cleaning
# ---------------------------------------------------------------------------
def task2_clean(utilities, substations, lines):
    print("Missing values (utilities/substations/lines):")
    print(utilities.isnull().sum().sum(), substations.isnull().sum().sum(), lines.isnull().sum().sum())

    substations["Latitude"] = pd.to_numeric(substations["Latitude"], errors="coerce")
    substations["Longitude"] = pd.to_numeric(substations["Longitude"], errors="coerce")
    substations["Capacity (MVA)"] = pd.to_numeric(substations["Capacity (MVA)"], errors="coerce")
    lines["Length (km)"] = pd.to_numeric(lines["Length (km)"], errors="coerce")

    utilities = utilities.drop_duplicates()
    substations = substations.drop_duplicates()
    lines = lines.drop_duplicates()
    return utilities, substations, lines


def validate_relationships(utilities_df, substations_df, lines_df):
    """Check for orphaned lines and dangling foreign keys."""
    valid_sub_ids = set(substations_df["Substation ID"])
    valid_utility_ids = set(utilities_df["Utility ID"])

    orphaned_source = lines_df[~lines_df["Source Substation ID"].isin(valid_sub_ids)]
    orphaned_dest = lines_df[~lines_df["Destination Substation ID"].isin(valid_sub_ids)]
    orphaned_utility = lines_df[~lines_df["Utility ID"].isin(valid_utility_ids)]

    return {
        "orphaned_source_lines": len(orphaned_source),
        "orphaned_destination_lines": len(orphaned_dest),
        "orphaned_utility_lines": len(orphaned_utility),
    }


# ---------------------------------------------------------------------------
# Task 3: Exploratory Data Analysis
# ---------------------------------------------------------------------------
def task3_eda(substations, lines):
    plt.figure(figsize=(10, 6))
    substations["Region"].value_counts().head(10).plot(
        kind="bar", title="Top Regions by Number of Substations")
    plt.xlabel("Region")
    plt.ylabel("Number of Substations")
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eda_regions.png"))
    plt.close()

    plt.figure(figsize=(10, 6))
    lines["Source Substation"].value_counts().head(10).plot(
        kind="bar", title="Top 10 Source Substations by Number of Lines")
    plt.xlabel("Substation")
    plt.ylabel("Number of Lines")
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eda_top_substations.png"))
    plt.close()

    print("Substations Numeric Summary:")
    print(substations[["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)"]].describe(), "\n")
    print("Substation Status Count:")
    print(substations["Status"].value_counts(), "\n")


# ---------------------------------------------------------------------------
# Task 4: Merging
# ---------------------------------------------------------------------------
def task4_merge(utilities, substations, lines):
    lines_with_source = lines.merge(
        substations[["Substation ID", "Name", "Region", "Country"]],
        left_on="Source Substation ID", right_on="Substation ID",
        how="left", suffixes=("", "_source"))

    lines_with_subs = lines_with_source.merge(
        substations[["Substation ID", "Name", "Region", "Country"]],
        left_on="Destination Substation ID", right_on="Substation ID",
        how="left", suffixes=("_source", "_dest"))

    lines_with_utility = lines_with_subs.merge(
        utilities[["Utility ID", "Name", "Code"]], on="Utility ID", how="left")

    top_lines = (lines_with_utility
                 .groupby(["Code", "Region_source"])
                 .size().reset_index(name="Line Count")
                 .sort_values(by="Line Count", ascending=False).head(10))
    print("Top 10 Utility/Region Combinations by Line Count:")
    print(top_lines, "\n")

    lines_with_utility.to_csv(os.path.join(DATA_DIR, "merged_lines.csv"), index=False)
    return lines_with_utility


# ---------------------------------------------------------------------------
# Task 5: Network analysis + N-1 contingency
# ---------------------------------------------------------------------------
def task5_network(substations, lines):
    G = nx.from_pandas_edgelist(
        lines, source="Source Substation", target="Destination Substation",
        edge_attr=["Length (km)", "Voltage (kV)"], create_using=nx.Graph())

    print(f"Number of nodes (substations): {G.number_of_nodes()}")
    print(f"Number of edges (lines): {G.number_of_edges()}")

    degree_centrality = nx.degree_centrality(G)
    top_substations = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 Substations by Degree Centrality:")
    for substation, centrality in top_substations:
        print(f"  {substation}: {centrality:.4f}")

    if top_substations:
        top_hub = top_substations[0][0]
        G_minus = G.copy()
        G_minus.remove_node(top_hub)
        print(f"\nConnected components before removing top hub ({top_hub}): "
              f"{nx.number_connected_components(G)}")
        print(f"Connected components after removing top hub: "
              f"{nx.number_connected_components(G_minus)}")

    plt.figure(figsize=(12, 8))
    nx.draw(G, with_labels=True, node_size=200, node_color="lightblue", font_size=6)
    plt.title("National Grid Substation Network")
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "network_graph.png"))
    plt.close()

    return G, degree_centrality


def create_grid_map(substations, lines):
    """Optional: requires `folium`. Produces an interactive HTML map."""
    import folium

    m = folium.Map(location=[7.9, -1.0], zoom_start=6)
    sub_lookup = substations.set_index("Substation ID")

    for _, sub in substations.iterrows():
        folium.CircleMarker(
            location=[sub["Latitude"], sub["Longitude"]],
            popup=f"{sub['Name']} ({sub['Voltage (kV)']} kV)",
            radius=4,
        ).add_to(m)

    for _, line in lines.iterrows():
        try:
            src = sub_lookup.loc[line["Source Substation ID"]]
            dst = sub_lookup.loc[line["Destination Substation ID"]]
            folium.PolyLine(
                locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
                weight=2,
            ).add_to(m)
        except KeyError:
            continue

    out_path = os.path.join(DATA_DIR, "substation_map.html")
    m.save(out_path)
    print(f"Map written to {out_path}")
    return m


def main():
    utilities, substations, lines = load_data()
    task1_inspect(utilities, substations, lines)
    utilities, substations, lines = task2_clean(utilities, substations, lines)
    print("Relationship validation:", validate_relationships(utilities, substations, lines), "\n")
    task3_eda(substations, lines)
    task4_merge(utilities, substations, lines)
    task5_network(substations, lines)


if __name__ == "__main__":
    main()
