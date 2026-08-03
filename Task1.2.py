import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

utilities = pd.read_csv("clean_utilities.csv")
substations = pd.read_csv("clean_substations.csv")
lines =  pd.read_csv("clean_lines.csv")

print(utilities.head())
print(substations.head())
print(lines.head())

print(substations.describe())
print(substations.columns)
type(substations)

print(substations["Status"].value_counts())
print(substations["Voltage (kV)"].value_counts())
print(substations["Region"].value_counts())

print(lines.head())

print(lines["Utility ID"].value_counts())
utility_counts = lines["Utility ID"].value_counts().reset_index()

print(utility_counts)

utility_counts = lines["Utility ID"].value_counts().reset_index()

utility_counts = utility_counts.merge(
    utilities[["Utility ID", "Name"]],
    on="Utility ID"
)

print(utility_counts)
print(utilities.columns)

#Connected substations
source_counts = lines["Source Substation"].value_counts()
print(source_counts)

#count destinations
destination_counts = lines["Destination Substation"].value_counts()
print(destination_counts)

connections = pd.DataFrame()

connections["Source Connections"] = source_counts
connections["Destination Connections"] = destination_counts
connections = connections.fillna(0)
print(connections)

connections["Total Connections"] = (
    connections["Source Connections"] +
    connections["Destination Connections"]
)
print(connections)

connections = connections.sort_values("Total Connections", ascending=False)
print(connections.head(10))

#Geographic distribution of substations
sub_region = substations[["Substation ID", "Region"]]
print(sub_region.head())

source_regions = lines.merge(sub_region, left_on="Source Substation ID", right_on="Substation ID")
source_region_count = source_regions["Region"].value_counts()
print(source_region_count)

#Destination regions
destination_regions = lines.merge(
    sub_region,
    left_on = "Destination Substation ID",
    right_on= "Substation ID"
)
destination_region_count = destination_regions["Region"].value_counts()
print(destination_region_count)

#Total regional connectivity
region_connections = source_region_count.add(
    destination_region_count,
    fill_value=0
)

region_connections = region_connections.sort_values(
    ascending = False
)

print(region_connections)

#Visualisation using bar chart
#Graph1: Number of substation
plt.figure(figsize=(10,6))

substations["Region"].value_counts().plot(kind="bar")

plt.title("Number of Substations by Region")
plt.xlabel("Region")
plt.ylabel("Number of Substations")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

#Graph2: Voltage distribution
plt.figure(figsize=(10,6))

substations["Voltage (kV)"].value_counts().sort_index().plot(
    kind="bar", color = "orange"
)
plt.title("Distribution of Voltage levels")
plt.xlabel("Voltage (kV)")
plt.ylabel("Number of Substations")

plt.tight_layout()

plt.show()

#Graph 3: Utilities operatng the most lines
plt.figure(figsize=(10,6))

plt.bar(
    utility_counts["Name"],
    utility_counts["count"],
    color = "green"
)
plt.title("Number of Lines Operated by Utility")
plt.xlabel("Utility")
plt.ylabel("Number of Lines")

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

#Graph 4: Top 10 Connected Substations
top10 = connections.head(10)

plt.figure(figsize=(10,6))

plt.barh(
    top10.index,
    top10["Total Connections"],
    color= "blue" 
)
plt.title("Top 10 Most connected Substations")
plt.xlabel("Total Connections")
plt.ylabel("Substation")

plt.tight_layout()

plt.show()

