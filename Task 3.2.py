import pandas as pd
import plotly.express as px


# TASK 3.2 - ADVANCED VISUALIZATIONS
# ANIMATED GRID EXPANSIO MAP


# Load the substation data
substations = pd.read_csv("substations.csv")

print("Data loaded successfully!")

# Check the dataset
print("\nAvailable columns:")
print(substations.columns.tolist())


# PREPARE THE DATA

# Remove rows with missing important information
animation_data = substations.dropna(
    subset=[
        "Latitude",
        "Longitude",
        "Commissioning Year"
    ]
).copy()

# Make sure Commissioning Year is numeric
animation_data["Commissioning Year"] = pd.to_numeric(
    animation_data["Commissioning Year"],
    errors="coerce"
)

# Remove invalid years
animation_data = animation_data.dropna(
    subset=["Commissioning Year"]
)

# Convert the year to an integer
animation_data["Commissioning Year"] = (
    animation_data["Commissioning Year"].astype(int)
)

# Sort substations by commissioning year
animation_data = animation_data.sort_values(
    "Commissioning Year"
)

# Print the years available
print("\nCommissioning Years:")
print(
    animation_data["Commissioning Year"]
    .value_counts()
    .sort_index()
)


# CREATE THE ANIMATED MAP


fig = px.scatter_geo(
    animation_data,
    lat="Latitude",
    lon="Longitude",
    animation_frame="Commissioning Year",
    hover_name="Name",
    hover_data={
        "Region": True,
        "Country": True,
        "Voltage (kV)": True,
        "Capacity (MVA)": True,
        "Commissioning Year": True,
        "Latitude": False,
        "Longitude": False
    },
    color="Voltage (kV)",
    size="Capacity (MVA)",
    size_max=25,
    projection="natural earth",
    title="Animated Expansion of the National Electricity Grid by Commissioning Year"
)

# Improve the appearance of the map
fig.update_geos(
    center=dict(
        lat=7.9,
        lon=-1.0
    ),
    projection_scale=5
)

# Improve animation speed
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300

# Show the animated map
fig.show()

# Save the map as an HTML file
fig.write_html("animated_grid_expansion_map.html")

print("\nAnimated grid expansion map created successfully!")
print("Saved as: animated_grid_expansion_map.html")