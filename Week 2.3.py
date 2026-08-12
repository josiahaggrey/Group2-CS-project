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

#Task 2.3: Business Intelligence & Reliability Analysis
#Part 1: Utility Footprint Analysis

utility_lines = (
    lines.groupby("Utility ID").size()
    .reset_index(name="Number of Lines")
)

utility_lines = utility_lines.merge(
    utilities[["Utility ID", "Name"]],
    on = "Utility ID",
    how = "left"
)

utility_lines = utility_lines.sort_values(
    "Number of Lines",
    ascending = False
)
print(utility_lines)

#Graph
plt.figure(figsize = (10,6))

plt.bar(
    utility_lines["Name"],
    utility_lines["Number of Lines"],
    color = "blue"
)
plt.title("Utility Footprint")
plt.xlabel("Utility")
plt.ylabel("Number of Lines")

plt.xticks(rotation = 45)
plt.tight_layout()
plt.show()

#Part 2: Utility Footprint by Region
lines_region = lines.merge(
    substations[["Substation ID", "Region"]],
    left_on = "Source Substation ID",
    right_on = "Substation ID",
    how ="left"
)
lines_region = lines_region.merge(
    utilities[["Utility ID", "Name"]],
    on = "Utility ID",
    how = "left"
)
utility_region = (
    lines_region.groupby(["Name", "Region"]).size().reset_index(name = "Line Count")
)
print(utility_region)

#Part 3: Capacity Analysis
highest_capacity = substations.sort_values(
    "Capacity (MVA)", ascending = False
)
print(highest_capacity.head(10))

#Graph
top_capacity = highest_capacity.head(10)
plt.figure(figsize = (10,6))
plt.barh(top_capacity["Name"], top_capacity["Capacity (MVA)"], color = "darkorange")
plt.title("Top 10 Highest Capacity Substations")
plt.xlabel("Capacity (MVA)")
plt.ylabel("Substation")
plt.tight_layout()
plt.show()


#Part 4: Growth Opportunities
region_growth = (
    substations["Region"].value_counts().sort_values()
)
print(region_growth)

#Graph
plt.figure(figsize = (10,6))
region_growth.plot(kind = "barh", color = "green")
plt.title("Substations by Region")
plt.xlabel("Number of Substations")
plt.tight_layout()
plt.show()


#Part 5: Technical Loss Proxy
lines["Loss Proxy"] = (lines["Length (km)"] / lines["Voltage (kV)"])
loss_proxy = lines.sort_values("Loss Proxy", ascending = False)
print(loss_proxy[["Source Substation", "Destination Substation", "Loss Proxy"]].head(10))


#Part 6:Asset Age
current_year = 2026
substations["Asset Age"] = (current_year - substations["Commissioning Year"])
oldest_assets = substations.sort_values("Asset Age", ascending = False)
print(oldest_assets.head(10))

#Histogram Graph
plt.figure(figsize = (10,6))
plt.hist(substations["Asset Age"], bins = 10,
         color = "purple", edgecolor = "black") 
plt.title("Distribution of Substation Ages")
plt.xlabel("Age (Years)")
plt.ylabel("Number of Substations")
plt.tight_layout()
plt.show()


#Part7: Reliability Analysis
maintenance = lines["Status"].value_counts()
print(maintenance)

maintenance_region = (lines_region.groupby(["Region", "Status"])
                      .size().reset_index(name = "Count"))

print(maintenance_region)

maintenance_percentage = (
    lines_region.groupby("Region")["Status"]
    .value_counts(normalize = True).mul(100)
    .rename("Percentage").reset_index()
)

under_maintenance = maintenance_percentage[
    maintenance_percentage["Status"] == "Under Maintenance"
]
print(under_maintenance)


#Part 8: Capacity Concentration
capacity_concentration = substations.sort_values("Capacity (MVA)", ascending = False)
print(capacity_concentration.head(10))

#Graph
top10 = capacity_concentration.head(10)
plt.figure(figsize = (10,6))
plt.bar(top10["Name"], top10["Capacity (MVA)"], color = "red")
plt.xticks(rotation = 45)
plt.title("Capacity Concentration in Top 10 Substations")
plt.ylabel("Capacity (MVA)")
plt.tight_layout()
plt.show()