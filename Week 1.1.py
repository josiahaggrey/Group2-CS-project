import pandas as pd

import numpy as np

# =====================================================
# LOAD DATASETS
# =====================================================
utilities = pd.read_csv("utilities.csv")
substations = pd.read_csv("substations.csv")
lines = pd.read_csv("lines.csv")

# =====================================================
# PREVIEW DATA
# =====================================================
print("========== SUBSTATIONS ==========")
print(substations.head())

print("\n========== LINES ==========")
print(lines.head())

print("\n========== UTILITIES ==========")
print(utilities.head())

# =====================================================
# DATASET INFORMATION
# =====================================================
print("\nSubstations Info")
substations.info()

print("\nLines Info")
lines.info()

print("\nUtilities Info")
utilities.info()

# =====================================================
# MISSING VALUES BEFORE CLEANING
# =====================================================
print("\nMissing Values (Substations)")
print(substations.isnull().sum())

print("\nMissing Values (Lines)")
print(lines.isnull().sum())

print("\nMissing Values (Utilities)")
print(utilities.isnull().sum())


# =====================================================
# CHECK FOR DUPLICATES
# =====================================================

print("\nSubstations")
print("Duplicate Rows:", substations.duplicated().sum())

print("\nLines")
print("Duplicate Rows:", lines.duplicated().sum())

print("\nUtilities")
print("Duplicate Rows:", utilities.duplicated().sum())

# =====================================================
# DROP DUPLICATES IF ANY
# =====================================================

utilities = utilities.drop_duplicates()

substations = substations.drop_duplicates()

lines = lines.drop_duplicates()


# =====================================================
# SAVE CLEAN DATASETS
# =====================================================

utilities.to_csv("utilities_cleaned.csv", index=False)
substations.to_csv("substations_cleaned.csv", index=False)
lines.to_csv("lines_cleaned.csv", index=False)


print("\nCleaning completed successfully!")

# ============================================================
#  DATA VALIDATION
# ============================================================

print("\n==============================")
print("      DATA VALIDATION")
print("==============================")

# ------------------------------------------------------------
# 1. Ensure Numeric Columns Are Truly Numeric
# ------------------------------------------------------------

substation_numeric = [
    "Substation ID",
    "Latitude",
    "Longitude",
    "Voltage (kV)",
    "Capacity (MVA)",
    "Commissioning Year"
]

line_numeric = [
    "Line ID",
    "Utility ID",
    "Source Substation ID",
    "Destination Substation ID",
    "Voltage (kV)",
    "Length (km)",
    "Capacity (MVA)"
]

utility_numeric = [
    "Utility ID"
]

# Convert columns to numeric
for column in substation_numeric:
    substations[column] = pd.to_numeric(substations[column], errors="coerce")

for column in line_numeric:
    lines[column] = pd.to_numeric(lines[column], errors="coerce")

for column in utility_numeric:
    utilities[column] = pd.to_numeric(utilities[column], errors="coerce")

print("\n✓ Numeric columns validated.")

# ------------------------------------------------------------
# 2. Check for Missing Values Created During Conversion
# ------------------------------------------------------------

print("\nMissing Values After Numeric Validation")

print("\nSubstations")
print(substations.isnull().sum())

print("\nLines")
print(lines.isnull().sum())

print("\nUtilities")
print(utilities.isnull().sum())

# ------------------------------------------------------------
# 3. Verify Every Source/Destination Substation Exists
# ------------------------------------------------------------

valid_substation_ids = set(substations["Substation ID"])

invalid_source = lines[
    ~lines["Source Substation ID"].isin(valid_substation_ids)
]

invalid_destination = lines[
    ~lines["Destination Substation ID"].isin(valid_substation_ids)
]

print("\nReferential Integrity Check")

print("Invalid Source IDs:", len(invalid_source))
print("Invalid Destination IDs:", len(invalid_destination))

if not invalid_source.empty:
    print("\nRows with Invalid Source IDs")
    print(invalid_source)

if not invalid_destination.empty:
    print("\nRows with Invalid Destination IDs")
    print(invalid_destination)

# ------------------------------------------------------------
# 4. Check for Duplicate Entries
# ------------------------------------------------------------

print("\nDuplicate Check")

print("Duplicate Utilities:", utilities.duplicated().sum())
print("Duplicate Substations:", substations.duplicated().sum())
print("Duplicate Lines:", lines.duplicated().sum())

if utilities.duplicated().any():
    print("\nDuplicate Utility Rows")
    print(utilities[utilities.duplicated()])

if substations.duplicated().any():
    print("\nDuplicate Substation Rows")
    print(substations[substations.duplicated()])

if lines.duplicated().any():
    print("\nDuplicate Line Rows")
    print(lines[lines.duplicated()])

# ------------------------------------------------------------
# 5. Validate Latitude and Longitude
# ------------------------------------------------------------

# Approximate West African geographic bounds
MIN_LAT = 4
MAX_LAT = 15

MIN_LON = -17
MAX_LON = 3

invalid_coordinates = substations[
    (substations["Latitude"] < MIN_LAT) |
    (substations["Latitude"] > MAX_LAT) |
    (substations["Longitude"] < MIN_LON) |
    (substations["Longitude"] > MAX_LON)
]

print("\nCoordinate Validation")

print("Invalid Coordinates:", len(invalid_coordinates))

if not invalid_coordinates.empty:
    print("\nRows with Invalid Coordinates")
    print(invalid_coordinates)

# ------------------------------------------------------------
# 6. Final Validation Summary
# ------------------------------------------------------------

print("\n==============================")
print(" VALIDATION SUMMARY")
print("==============================")

print(f"Duplicate Utilities: {utilities.duplicated().sum()}")
print(f"Duplicate Substations: {substations.duplicated().sum()}")
print(f"Duplicate Lines: {lines.duplicated().sum()}")

print(f"Invalid Source IDs: {len(invalid_source)}")
print(f"Invalid Destination IDs: {len(invalid_destination)}")
print(f"Invalid Coordinates: {len(invalid_coordinates)}")

print("\nRemaining Missing Values")

print("Utilities:")
print(utilities.isnull().sum().sum())

print("Substations:")
print(substations.isnull().sum().sum())

print("Lines:")
print(lines.isnull().sum().sum())

print("\nData validation completed.")