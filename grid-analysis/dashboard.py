"""
Task 3.1: Comprehensive Dashboard Development (Week 3, National Electricity
Grid Network Analysis component).

Integrates the outputs of Tasks 1.1-1.3 (cleaning, EDA, integration) into
one interactive Streamlit app, per the course spec's five required tabs:
Overview, Network, Geography, Reliability, Search. Network centrality,
N-1 contingency, and business-intelligence metrics are computed directly
here with NetworkX/pandas rather than read from separate Task 2.1-2.3
report files - the team hasn't produced those as standalone deliverables
yet (see grid-analysis/README.md), so this dashboard computes what it
needs on the fly instead of waiting on them.

Run:
    streamlit run dashboard.py

All figures/maps use Plotly (matching the course spec's own Task 3.1
sample imports: streamlit, plotly.express, plotly.graph_objects) so
everything stays interactive inside Streamlit without an extra mapping
dependency like streamlit-folium.
"""
import os

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CLEAN_DIR = os.path.join(DATA_DIR, "cleaned")

st.set_page_config(page_title="National Grid Dashboard", layout="wide")


# ---------------------------------------------------------------------------
# Data loading (cached so filtering/interaction doesn't re-read CSVs)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    substations = pd.read_csv(os.path.join(CLEAN_DIR, "substations_clean.csv"))
    lines = pd.read_csv(os.path.join(CLEAN_DIR, "lines_clean.csv"))
    utilities = pd.read_csv(os.path.join(CLEAN_DIR, "utilities_clean.csv"))
    lines = lines.merge(
        utilities[["Utility ID", "Alias"]], on="Utility ID", how="left"
    ).rename(columns={"Alias": "Utility"})
    return substations, lines, utilities


@st.cache_resource
def build_graph(substations, lines):
    """One undirected graph for the whole network - AC power flow has no
    fixed direction, matching the convention grid-analysis/tasks already
    uses. Node/edge attributes carry everything the Network and Geography
    tabs need without re-joining back to the DataFrames each time."""
    graph = nx.Graph()
    for _, row in substations.iterrows():
        graph.add_node(
            row["Substation ID"], name=row["Short Name"], region=row["Region"],
            country=row["Country"], voltage=row["Voltage (kV)"],
            capacity=row["Capacity (MVA)"], lat=row["Latitude"], lon=row["Longitude"],
            status=row["Status"], commissioning_year=row["Commissioning Year"],
        )
    for _, row in lines.iterrows():
        graph.add_edge(
            row["Source Substation ID"], row["Destination Substation ID"],
            length=row["Length (km)"], capacity=row["Capacity (MVA)"],
            status=row["Status"], voltage=row["Voltage (kV)"], utility=row["Utility"],
        )
    return graph


substations, lines, utilities = load_data()
graph = build_graph(substations, lines)

st.title("National Electricity Grid Dashboard")
st.caption(
    "Synthetic, illustrative dataset grounded in Ghanaian geography and utility "
    "names (see grid-analysis/README.md) - not verified measurements of Ghana's "
    "actual electricity infrastructure."
)

tab_overview, tab_network, tab_geography, tab_reliability, tab_search = st.tabs(
    ["Overview", "Network", "Geography", "Reliability", "Search"]
)


# ---------------------------------------------------------------------------
# Overview tab - executive summary
# ---------------------------------------------------------------------------
with tab_overview:
    total_capacity = substations["Capacity (MVA)"].sum()
    active_line_pct = (lines["Status"] == "Active").mean() * 100
    density = nx.density(graph)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Substations", len(substations))
    col2.metric("Lines", len(lines))
    col3.metric("Utilities", len(utilities))
    col4.metric("Total Capacity", f"{total_capacity:,.0f} MVA")
    col5.metric("Lines Active", f"{active_line_pct:.0f}%")
    col6.metric("Network Density", f"{density:.3f}")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        region_counts = substations["Region"].value_counts().reset_index()
        region_counts.columns = ["Region", "Substations"]
        fig = px.bar(region_counts, x="Region", y="Substations",
                     title="Substations by Region")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        voltage_counts = substations["Voltage (kV)"].value_counts().sort_index().reset_index()
        voltage_counts.columns = ["Voltage (kV)", "Substations"]
        fig = px.bar(voltage_counts, x="Voltage (kV)", y="Substations",
                     title="Substations by Voltage Level")
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Network tab - centrality, structure, N-1 contingency
# ---------------------------------------------------------------------------
with tab_network:
    st.subheader("Network Structure")

    region_filter = st.multiselect(
        "Filter by region", sorted(substations["Region"].unique()),
        default=[], key="network_region_filter",
        help="Leave empty to include the whole network.",
    )

    if region_filter:
        keep_nodes = [n for n, d in graph.nodes(data=True) if d["region"] in region_filter]
        view = graph.subgraph(keep_nodes).copy()
    else:
        view = graph

    if view.number_of_nodes() == 0:
        st.warning("No substations match this filter.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Nodes in view", view.number_of_nodes())
        col2.metric("Edges in view", view.number_of_edges())
        col3.metric("Connected components", nx.number_connected_components(view))

        degree_centrality = nx.degree_centrality(view)
        betweenness = nx.betweenness_centrality(view)

        centrality_df = pd.DataFrame({
            "Substation": [view.nodes[n]["name"] for n in view.nodes],
            "Region": [view.nodes[n]["region"] for n in view.nodes],
            "Degree Centrality": [degree_centrality[n] for n in view.nodes],
            "Betweenness Centrality": [betweenness[n] for n in view.nodes],
        }).sort_values("Degree Centrality", ascending=False)

        left, right = st.columns([2, 1])
        with left:
            pos = nx.spring_layout(view, seed=42)
            edge_x, edge_y = [], []
            for u, v in view.edges():
                edge_x += [pos[u][0], pos[v][0], None]
                edge_y += [pos[u][1], pos[v][1], None]
            edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                                     line=dict(width=1, color="#9aa0b4"), hoverinfo="none")

            node_x = [pos[n][0] for n in view.nodes]
            node_y = [pos[n][1] for n in view.nodes]
            node_size = [10 + degree_centrality[n] * 60 for n in view.nodes]
            node_text = [f"{view.nodes[n]['name']} ({view.nodes[n]['region']})<br>"
                         f"Degree centrality: {degree_centrality[n]:.3f}" for n in view.nodes]
            node_trace = go.Scatter(
                x=node_x, y=node_y, mode="markers", hoverinfo="text", text=node_text,
                marker=dict(size=node_size, color=[view.nodes[n]["voltage"] for n in view.nodes],
                            colorscale="Viridis", showscale=True, colorbar=dict(title="kV")),
            )
            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(showlegend=False, title="Force-directed network layout "
                               "(node size = degree centrality, color = voltage)",
                               xaxis=dict(visible=False), yaxis=dict(visible=False),
                               height=520)
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.markdown("**Top substations by degree centrality**")
            st.dataframe(centrality_df.head(10).reset_index(drop=True), hide_index=True,
                         use_container_width=True)

        st.markdown("---")
        st.subheader("N-1 Contingency Analysis")
        st.caption(
            "Removes one substation and checks whether the network fragments - a "
            "simplified proxy for the real contingency studies grid operators run "
            "before scheduling maintenance. Not a substitute for power-flow analysis."
        )
        options = sorted(view.nodes, key=lambda n: view.nodes[n]["name"])
        chosen = st.selectbox(
            "Substation to remove", options,
            format_func=lambda n: f"{view.nodes[n]['name']} ({view.nodes[n]['region']})",
        )
        before = nx.number_connected_components(view)
        reduced = view.copy()
        reduced.remove_node(chosen)
        after = nx.number_connected_components(reduced)

        col1, col2, col3 = st.columns(3)
        col1.metric("Components before removal", before)
        col2.metric("Components after removal", after)
        col3.metric("Change", f"+{after - before}" if after > before else "0")

        if after > before:
            st.error(
                f"Removing {view.nodes[chosen]['name']} fragments the network into "
                f"{after} components - a single point of failure in this view."
            )
        else:
            st.success(
                f"Removing {view.nodes[chosen]['name']} does not fragment the network "
                f"in this view - the remaining substations stay connected to each other."
            )


# ---------------------------------------------------------------------------
# Geography tab - national map with overlays
# ---------------------------------------------------------------------------
with tab_geography:
    st.subheader("Geographic Overlay")

    col1, col2, col3 = st.columns(3)
    with col1:
        geo_regions = st.multiselect("Region", sorted(substations["Region"].unique()),
                                      key="geo_region")
    with col2:
        geo_voltages = st.multiselect("Voltage (kV)", sorted(substations["Voltage (kV)"].unique()),
                                       key="geo_voltage")
    with col3:
        geo_utilities = st.multiselect("Utility", sorted(lines["Utility"].dropna().unique()),
                                        key="geo_utility")

    sub_view = substations.copy()
    if geo_regions:
        sub_view = sub_view[sub_view["Region"].isin(geo_regions)]
    if geo_voltages:
        sub_view = sub_view[sub_view["Voltage (kV)"].isin(geo_voltages)]

    line_view = lines.copy()
    if geo_utilities:
        line_view = line_view[line_view["Utility"].isin(geo_utilities)]
    visible_ids = set(sub_view["Substation ID"])
    line_view = line_view[
        line_view["Source Substation ID"].isin(visible_ids)
        & line_view["Destination Substation ID"].isin(visible_ids)
    ]

    sub_lookup = substations.set_index("Substation ID")
    fig = go.Figure()

    for status, color in [("Active", "#2f8f52"), ("Under Maintenance", "#e8a33d")]:
        subset = line_view[line_view["Status"] == status]
        lat_pairs, lon_pairs = [], []
        for _, row in subset.iterrows():
            src = sub_lookup.loc[row["Source Substation ID"]]
            dst = sub_lookup.loc[row["Destination Substation ID"]]
            lat_pairs += [src["Latitude"], dst["Latitude"], None]
            lon_pairs += [src["Longitude"], dst["Longitude"], None]
        if lat_pairs:
            fig.add_trace(go.Scattergeo(
                lat=lat_pairs, lon=lon_pairs, mode="lines",
                line=dict(width=1.5, color=color), name=f"Line: {status}",
            ))

    fig.add_trace(go.Scattergeo(
        lat=sub_view["Latitude"], lon=sub_view["Longitude"], mode="markers",
        marker=dict(size=6 + sub_view["Capacity (MVA)"] / 40,
                    color=sub_view["Voltage (kV)"], colorscale="Viridis",
                    showscale=True, colorbar=dict(title="kV")),
        text=sub_view["Name"] + " - " + sub_view["Region"] + " ("
             + sub_view["Voltage (kV)"].astype(str) + " kV, "
             + sub_view["Capacity (MVA)"].astype(str) + " MVA)",
        hoverinfo="text", name="Substation",
    ))

    fig.update_geos(
        scope="africa", center=dict(lat=7.9, lon=-1.0), projection_scale=6,
        showcountries=True, showland=True, landcolor="#1f2430",
    )
    fig.update_layout(height=600, title="Substations and lines "
                       f"({len(sub_view)} substations, {len(line_view)} lines shown)")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Reliability tab - business intelligence
# ---------------------------------------------------------------------------
with tab_reliability:
    st.subheader("Business Intelligence & Reliability")

    utility_footprint = (
        lines.groupby("Utility")
        .agg(Lines=("Line ID", "count"), Total_Capacity=("Capacity (MVA)", "sum"))
        .reset_index().sort_values("Lines", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(utility_footprint, x="Utility", y="Lines",
                     title="Lines Operated per Utility")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        maintenance = lines["Status"].value_counts(normalize=True).mul(100).reset_index()
        maintenance.columns = ["Status", "Percent"]
        fig = px.pie(maintenance, names="Status", values="Percent",
                     title="Line Status", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        fig = px.histogram(substations, x="Commissioning Year", nbins=20,
                            title="Asset Age Profile (Commissioning Year)")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.box(substations, x="Voltage (kV)", y="Capacity (MVA)",
                     title="Capacity Distribution by Voltage Tier")
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Regions with the fewest substations (potential growth areas)**")
    growth = substations["Region"].value_counts().sort_values().reset_index()
    growth.columns = ["Region", "Substations"]
    st.dataframe(growth.head(5), hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Search tab - substation finder and utility comparison
# ---------------------------------------------------------------------------
with tab_search:
    st.subheader("Substation Finder")
    degree_centrality_full = nx.degree_centrality(graph)

    name_to_id = dict(zip(substations["Name"], substations["Substation ID"]))
    chosen_name = st.selectbox("Search for a substation", sorted(name_to_id.keys()))
    chosen_id = name_to_id[chosen_name]
    record = substations[substations["Substation ID"] == chosen_id].iloc[0]
    connected_lines = lines[
        (lines["Source Substation ID"] == chosen_id) | (lines["Destination Substation ID"] == chosen_id)
    ]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Region", record["Region"])
    col2.metric("Voltage", f"{record['Voltage (kV)']} kV")
    col3.metric("Capacity", f"{record['Capacity (MVA)']} MVA")
    col4.metric("Connections", len(connected_lines))

    col1, col2 = st.columns(2)
    col1.metric("Commissioned", int(record["Commissioning Year"]))
    col2.metric("Degree Centrality Rank",
                f"#{sorted(degree_centrality_full.values(), reverse=True).index(degree_centrality_full[chosen_id]) + 1} "
                f"of {len(degree_centrality_full)}")

    if len(connected_lines):
        st.markdown("**Connected lines**")
        st.dataframe(
            connected_lines[["Source Substation", "Destination Substation", "Voltage (kV)",
                              "Length (km)", "Status"]].reset_index(drop=True),
            hide_index=True, use_container_width=True,
        )

    st.markdown("---")
    st.subheader("Utility Comparison")
    compare_utilities = st.multiselect(
        "Compare utilities", sorted(lines["Utility"].dropna().unique()),
        default=sorted(lines["Utility"].dropna().unique())[:2],
    )
    if len(compare_utilities) >= 1:
        compare_df = (
            lines[lines["Utility"].isin(compare_utilities)]
            .groupby("Utility")
            .agg(Lines=("Line ID", "count"), **{"Total Capacity (MVA)": ("Capacity (MVA)", "sum")},
                 **{"Avg. Length (km)": ("Length (km)", "mean")})
            .reset_index()
        )
        st.dataframe(compare_df, hide_index=True, use_container_width=True)
        fig = px.bar(compare_df, x="Utility", y="Lines", title="Lines Operated (Selected Utilities)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least one utility to compare.")
