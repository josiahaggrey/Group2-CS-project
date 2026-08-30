import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from geopy.distance import geodesic
from folium.plugins import HeatMap

# LOAD DATA
utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

print("Data loaded successfully!")

print("\nSubstations:")
print(substations.head())

print("\nLines:")
print(lines.head())

print("\nUtilities:")
print(utilities.head())

print("\nSubstation columns:")
print(substations.columns.tolist())

print("\nLine columns:")
print(lines.columns.tolist())

# SUBSTATION LOCATION MAP

fig = px.scatter_geo(
    substations,
    lat="Latitude",
    lon="Longitude",
    hover_name="Name",
    color="Voltage (kV)",
    title="National Grid Substation Locations",
    projection="natural earth"
)

fig.show()
fig.write_html("substation_map.html")

# DISTANCE ANALYSIS

print("\nDistance Analysis:")

line_distances = []

for _, line in lines.iterrows():

    source_id = line["Source Substation ID"]
    destination_id = line["Destination Substation ID"]

    source = substations[
        substations["Substation ID"] == source_id
    ].iloc[0]

    destination = substations[
        substations["Substation ID"] == destination_id
    ].iloc[0]

    source_coordinates = (
        source["Latitude"],
        source["Longitude"]
    )

    destination_coordinates = (
        destination["Latitude"],
        destination["Longitude"]
    )

    distance = geodesic(
        source_coordinates,
        destination_coordinates
    ).kilometers

    line_distances.append(distance)

print("Total transmission lines:", len(line_distances))
print(
    "Average line distance:",
    round(sum(line_distances) / len(line_distances), 2),
    "km"
)
print("Shortest line:", round(min(line_distances), 2), "km")
print("Longest line:", round(max(line_distances), 2), "km")

# TRANSMISSION LINE DISTANCE CATEGORIES

short_lines = []
medium_lines = []
long_lines = []

for distance in line_distances:

    if distance < 50:
        short_lines.append(distance)

    elif distance <= 150:
        medium_lines.append(distance)

    else:
        long_lines.append(distance)

print("\nTransmission Line Distance Categories:")
print("Short lines:", len(short_lines))
print("Medium lines:", len(medium_lines))
print("Long lines:", len(long_lines))

# SUBSTATION DENSITY BY REGION

print("\nSubstation Density by Region:")

region_counts = substations["Region"].value_counts()

for region, count in region_counts.items():
    print(f"{region}: {count} substations")

# HIGH-CAPACITY SUBSTATION ANALYSIS

print("\nHigh-Capacity Substations:")

high_capacity = substations[
    substations["Capacity (MVA)"] >=
    substations["Capacity (MVA)"].quantile(0.75)
]

print(
    "Number of high-capacity substations:",
    len(high_capacity)
)

print(
    high_capacity[
        [
            "Substation ID",
            "Name",
            "Region",
            "Capacity (MVA)",
            "Latitude",
            "Longitude"
        ]
    ]
)


# High-capacity substation map

fig_high_capacity = px.scatter_geo(
    high_capacity,
    lat="Latitude",
    lon="Longitude",
    hover_name="Name",
    hover_data=["Region", "Capacity (MVA)"],
    title="Geographic Distribution of High-Capacity Substations",
    projection="natural earth"
)

fig_high_capacity.show()
fig_high_capacity.write_html(
    "high_capacity_substations.html"
)

# GEOGRAPHIC COVERAGE GAPS
print("\nPotential Geographic Coverage Gaps:")

average_substations = region_counts.mean()

print(
    "Average substations per region:",
    round(average_substations, 2)
)

low_coverage_regions = region_counts[
    region_counts < average_substations
]

print("\nRegions with below-average substation coverage:")

for region, count in low_coverage_regions.items():
    print(f"{region}: {count} substations")

# UTILITY NETWORK ANALYSIS

print("\nUtility Network Analysis:")

utility_line_counts = lines["Utility ID"].value_counts()

for utility_id, count in utility_line_counts.items():
    print(
        f"Utility {utility_id}: "
        f"{count} transmission lines"
    )

# UTILITY TRANSMISSION LINE MAP

fig_lines = go.Figure()

for utility_id in lines["Utility ID"].unique():

    utility_lines = lines[
        lines["Utility ID"] == utility_id
    ]

    for _, line in utility_lines.iterrows():

        source = substations[
            substations["Substation ID"] ==
            line["Source Substation ID"]
        ].iloc[0]

        destination = substations[
            substations["Substation ID"] ==
            line["Destination Substation ID"]
        ].iloc[0]

        fig_lines.add_trace(
            go.Scattergeo(
                lon=[
                    source["Longitude"],
                    destination["Longitude"]
                ],
                lat=[
                    source["Latitude"],
                    destination["Latitude"]
                ],
                mode="lines",
                name=f"Utility {utility_id}",
                showlegend=True
            )
        )

fig_lines.update_layout(
    title="Transmission Line Networks by Utility",
    geo=dict(
        projection_type="natural earth"
    )
)

fig_lines.show()
fig_lines.write_html(
    "utility_transmission_networks.html"
)

# TRANSMISSION LINE DENSITY HEATMAP
line_midpoints = []

for _, line in lines.iterrows():

    source = substations[
        substations["Substation ID"] ==
        line["Source Substation ID"]
    ].iloc[0]

    destination = substations[
        substations["Substation ID"] ==
        line["Destination Substation ID"]
    ].iloc[0]

    midpoint_lat = (
        source["Latitude"] +
        destination["Latitude"]
    ) / 2

    midpoint_lon = (
        source["Longitude"] +
        destination["Longitude"]
    ) / 2

    line_midpoints.append({
        "Latitude": midpoint_lat,
        "Longitude": midpoint_lon
    })

line_midpoints_df = pd.DataFrame(line_midpoints)

fig_heatmap = px.density_map(
    line_midpoints_df,
    lat="Latitude",
    lon="Longitude",
    radius=20,
    zoom=5,
    center={
        "lat": 7.9,
        "lon": -1.0
    },
    title="Transmission Line Density Heatmap"
)

fig_heatmap.show()
fig_heatmap.write_html(
    "transmission_line_density_heatmap.html"
)

# REGIONAL AND CROSS-BORDER CONNECTIVITY

print("\nRegional and Cross-Border Connectivity:")

country_counts = substations["Country"].value_counts()

print("\nSubstations by country:")

for country, count in country_counts.items():
    print(f"{country}: {count} substations")


# Identify cross-border transmission lines

print("\nCross-Border Transmission Lines:")

cross_border_lines = []

for _, line in lines.iterrows():

    source = substations[
        substations["Substation ID"] ==
        line["Source Substation ID"]
    ].iloc[0]

    destination = substations[
        substations["Substation ID"] ==
        line["Destination Substation ID"]
    ].iloc[0]

    if source["Country"] != destination["Country"]:

        cross_border_lines.append({
            "Source": source["Name"],
            "Source Country": source["Country"],
            "Destination": destination["Name"],
            "Destination Country": destination["Country"]
        })

print(
    "Number of cross-border lines:",
    len(cross_border_lines)
)

for connection in cross_border_lines:

    print(
        connection["Source"],
        "(" + connection["Source Country"] + ")",
        "->",
        connection["Destination"],
        "(" + connection["Destination Country"] + ")"
    )


# Cross-border connectivity summary

cross_border_connections = {}

for connection in cross_border_lines:

    source_country = connection["Source Country"]
    destination_country = connection["Destination Country"]

    cross_border_connections[source_country] = (
        cross_border_connections.get(source_country, 0) + 1
    )

    cross_border_connections[destination_country] = (
        cross_border_connections.get(destination_country, 0) + 1
    )

print("\nCross-Border Connections by Country:")

for country, count in sorted(
    cross_border_connections.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(f"{country}: {count} connections")

# DISTANCE DISTRIBUTION CHART

categories = ["Short", "Medium", "Long"]

counts = [
    len(short_lines),
    len(medium_lines),
    len(long_lines)
]

plt.figure(figsize=(8, 5))

plt.bar(categories, counts)

plt.title("Transmission Line Distance Distribution")
plt.xlabel("Distance Category")
plt.ylabel("Number of Transmission Lines")

for i, count in enumerate(counts):

    plt.text(
        i,
        count + 0.5,
        str(count),
        ha="center"
    )

plt.tight_layout()
plt.show()

# FINAL INTERACTIVE MULTI-LAYER MAP

multi_map = folium.Map(
    location=[7.5, -1.5],
    zoom_start=6
)

# Layer 1: All substations

all_substations = folium.FeatureGroup(
    name="All Substations"
)

for _, row in substations.iterrows():

    folium.CircleMarker(
        location=[
            row["Latitude"],
            row["Longitude"]
        ],
        radius=5,
        color="blue",
        fill=True,
        fill_opacity=0.7,
        popup=(
            f"<b>{row['Name']}</b><br>"
            f"Substation ID: "
            f"{row['Substation ID']}<br>"
            f"Country: {row['Country']}<br>"
            f"Region: {row['Region']}<br>"
            f"Voltage: "
            f"{row['Voltage (kV)']} kV<br>"
            f"Capacity: "
            f"{row['Capacity (MVA)']} MVA"
        )
    ).add_to(all_substations)

all_substations.add_to(multi_map)

# Layer 2: High-capacity substations
high_capacity_layer = folium.FeatureGroup(
    name="High-Capacity Substations"
)

for _, row in high_capacity.iterrows():

    folium.Marker(
        location=[
            row["Latitude"],
            row["Longitude"]
        ],
        popup=(
            f"<b>{row['Name']}</b><br>"
            f"Substation ID: "
            f"{row['Substation ID']}<br>"
            f"Region: {row['Region']}<br>"
            f"Capacity: "
            f"{row['Capacity (MVA)']} MVA"
        ),
        tooltip="High-Capacity Substation"
    ).add_to(high_capacity_layer)

high_capacity_layer.add_to(multi_map)

# Layer 3: Transmission lines

transmission_lines = folium.FeatureGroup(
    name="Transmission Lines"
)

for _, line in lines.iterrows():

    source = substations[
        substations["Substation ID"] ==
        line["Source Substation ID"]
    ].iloc[0]

    destination = substations[
        substations["Substation ID"] ==
        line["Destination Substation ID"]
    ].iloc[0]

    folium.PolyLine(
        locations=[
            [
                source["Latitude"],
                source["Longitude"]
            ],
            [
                destination["Latitude"],
                destination["Longitude"]
            ]
        ],
        weight=2,
        opacity=0.7,
        popup=(
            f"Line ID: {line['Line ID']}<br>"
            f"Source: {source['Name']}<br>"
            f"Destination: {destination['Name']}"
        )
    ).add_to(transmission_lines)

transmission_lines.add_to(multi_map)

# Layer 4: Transmission line density
heatmap_layer = folium.FeatureGroup(
    name="Transmission Line Density"
)

heat_data = line_midpoints_df[
    ["Latitude", "Longitude"]
].values.tolist()

HeatMap(
    heat_data,
    radius=20,
    blur=15
).add_to(heatmap_layer)

heatmap_layer.add_to(multi_map)

# Layer control
folium.LayerControl().add_to(multi_map)

# Save final map
multi_map.save("final_interactive_multi_layer_map.html")
print("\nFinal interactive multi-layer map created successfully!")
print("Saved as: final_interactive_multi_layer_map.html")