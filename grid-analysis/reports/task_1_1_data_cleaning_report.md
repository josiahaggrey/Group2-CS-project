# Task 1.1 - Data Cleaning and Preprocessing Report

_Generated 2026-08-02T13:34:24_

## 1. Raw dataset inspection

### utilities

- Shape: 10 rows x 7 columns

- Duplicate rows (raw): 0

- Columns with missing values (raw): none

### substations

- Shape: 44 rows x 12 columns

- Duplicate rows (raw): 0

- Columns with missing values (raw): none

### lines

- Shape: 55 rows x 11 columns

- Duplicate rows (raw): 0

- Columns with missing values (raw): none


## 2. Missing-value handling strategy

- **utilities:** Categorical/text fields (Name, Alias, Code, Type, Country, Active): no imputation - a missing utility identity is a data-collection defect that must be corrected at the source, not guessed. Rows with a missing 'Utility ID' are dropped as unusable.

- **substations:** Numeric fields (Latitude, Longitude, Capacity (MVA), Commissioning Year): left as NaN and flagged, never imputed - substituting a fabricated coordinate or capacity would be actively misleading for network/geospatial analysis. Categorical fields (Region, Type, Status): missing values are labelled 'Unknown' so the row survives filtering/grouping instead of silently vanishing from region-level aggregates.

- **lines:** Numeric fields (Length (km), Capacity (MVA)): left as NaN and flagged - length can be recomputed from source/destination coordinates via the haversine formula where both substations are known, so that is the intended fallback rather than a blind fill. Status/Line Type: missing values are labelled 'Unknown' rather than assumed 'Active'/'Overhead', since assuming the optimistic default would understate risk in reliability analysis.


## 3. Transformations applied

- Rows dropped for missing primary key - utilities: 0, substations: 0, lines: 0

- Standardised missing-value spellings (['\\N', 'NULL', 'null', '', ' ', 'NA', 'N/A']) to NaN before any other processing.

- Coerced declared numeric columns via pd.to_numeric(errors='coerce') and recorded any values that failed to convert.

- Filled missing categorical fields (Region/Type/Status/Country/Line Type) with 'Unknown' rather than dropping the row.

- Removed exact full-row duplicates from each dataset.


## 4. Data quality assessment

- **Duplicate Utility IDs:** none found.

- **Duplicate Substation IDs:** none found.

- **Duplicate Line IDs:** none found.

- **Lines with an orphaned Source Substation ID:** none found.

- **Lines with an orphaned Destination Substation ID:** none found.

- **Lines with an orphaned Utility ID:** none found.

- **Substations with coordinates outside the plausible West Africa bounding box (lat (4.0, 15.0), lon (-18.0, 5.0)):** none found.

- **Substation numeric columns with non-numeric values:** none found.

- **Line numeric columns with non-numeric values:** none found.


## 5. Basic statistics summary (post-cleaning)

### substations

| stat  | Latitude | Longitude | Voltage (kV) | Capacity (MVA) | Commissioning Year |
| ----- | -------- | --------- | ------------ | -------------- | ------------------ |
| count | 44.0     | 44.0      | 44.0         | 44.0           | 44.0               |
| mean  | 6.9      | -1.19     | 134.55       | 157.87         | 1996.3             |
| std   | 1.88     | 2.31      | 120.4        | 139.92         | 16.11              |
| min   | 4.87     | -13.58    | 11.0         | 6.4            | 1967.0             |
| 25%   | 5.59     | -1.76     | 33.0         | 43.82          | 1982.25            |
| 50%   | 6.18     | -0.8      | 69.0         | 108.55         | 1999.5             |
| 75%   | 7.36     | -0.17     | 161.0        | 254.35         | 2009.25            |
| max   | 11.2     | 2.43      | 330.0        | 487.6          | 2022.0             |


### lines

| stat  | Voltage (kV) | Length (km) | Capacity (MVA) |
| ----- | ------------ | ----------- | -------------- |
| count | 55.0         | 55.0        | 55.0           |
| mean  | 141.38       | 99.31       | 222.4          |
| std   | 135.17       | 90.28       | 109.18         |
| min   | 11.0         | 3.8         | 32.9           |
| 25%   | 22.0         | 42.9        | 134.55         |
| 50%   | 69.0         | 75.9        | 229.9          |
| 75%   | 330.0        | 129.6       | 292.1          |
| max   | 330.0        | 426.0       | 506.3          |



## 6. Output

- `data/cleaned/utilities_clean.csv`

- `data/cleaned/substations_clean.csv`

- `data/cleaned/lines_clean.csv`
