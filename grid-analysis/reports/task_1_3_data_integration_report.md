# Task 1.3 - Data Integration and Relationship Mapping Report

_Generated 2026-08-02T16:15:37_

_Source: `data/cleaned/*.csv` (Task 1.1 output)._

See also: [Entity-Relationship Diagram](../docs/entity_relationship_diagram.md), [Data Dictionary](../docs/data_dictionary.md).


## 1. Foreign-key relationships established

- `lines.Utility ID` -> `utilities.Utility ID` (many lines per utility)

- `lines.Source Substation ID` -> `substations.Substation ID` (many lines originate at one substation)

- `lines.Destination Substation ID` -> `substations.Substation ID` (many lines terminate at one substation)


## 2. Orphaned-record handling

- Raw (cleaned) line count before integration: 55

- Orphaned lines found (Source/Destination Substation ID or Utility ID not present in the reference tables): 0

- No orphaned lines found - every line's foreign keys resolve correctly.

- Line count after removing orphans (input to the join): 55


## 3. Join operation and validation

- Master dataset shape: 55 rows x 39 columns

- Join type: left join (lines as the base table), so every surviving line is guaranteed one row in the master dataset - no fan-out, no silent drops.

- **Validation passed:** row count preserved exactly (55 in, 55 out) and every row has a matching source substation, destination substation, and utility.


## 4. Lookup dictionaries

- `substations_lookup.json`: 44 entries, keyed by Substation ID.

- `utilities_lookup.json`: 10 entries, keyed by Utility ID.

- Example: `substations_lookup[1]` = `{'name': 'Achimota Substation', 'short_name': 'Achimota', 'region': 'Greater Accra', 'country': 'Ghana', 'latitude': 5.6085, 'longitude': -0.2193, 'voltage_kv': 11, 'capacity_mva': 6.4, 'commissioning_year': 2008, 'type': 'Distribution', 'status': 'Active'}`


## 5. Master dataset preview

| row | Line ID | Source Name         | Source Region | Destination Name    | Destination Region | Utility Alias | Voltage (kV) | Length (km) |
| --- | ------- | ------------------- | ------------- | ------------------- | ------------------ | ------------- | ------------ | ----------- |
| 0   | 1       | Achimota Substation | Greater Accra | Tema Substation     | Greater Accra      | NEDCo         | 11           | 25.2        |
| 1   | 2       | Achimota Substation | Greater Accra | Mallam Substation   | Greater Accra      | NEDCo         | 11           | 11.0        |
| 2   | 3       | Achimota Substation | Greater Accra | Kaneshie Substation | Greater Accra      | GRIDCo        | 11           | 5.9         |
| 3   | 4       | Tema Substation     | Greater Accra | Mallam Substation   | Greater Accra      | ECG           | 330          | 34.4        |
| 4   | 5       | Tema Substation     | Greater Accra | Legon Substation    | Greater Accra      | GRIDCo        | 161          | 19.5        |


## 6. Output

- `data/integrated/master_dataset.csv`

- `data/integrated/substations_lookup.json`

- `data/integrated/utilities_lookup.json`
