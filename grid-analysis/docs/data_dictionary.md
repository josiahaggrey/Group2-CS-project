# Data Dictionary — National Electricity Grid Network Analysis

Covers the three source datasets (as cleaned by Task 1.1, in `data/cleaned/`)
and the integrated master dataset produced by Task 1.3
(`data/integrated/master_dataset.csv`). All coordinates, capacities,
commissioning years, and connections are **synthetic and illustrative** —
see the project spec's dataset-generation notes.

## utilities.csv / utilities_clean.csv

| Column | Type | Description |
|---|---|---|
| `Utility ID` | int64 | Unique integer identifier. Primary key. |
| `Name` | string | Full legal name of the utility. |
| `Alias` | string | Common short name (e.g. ECG, GRIDCo). |
| `Code` | string | Three-letter code used to cross-reference the utility elsewhere in the dataset. |
| `Type` | string | One of `Generation`, `Transmission`, `Distribution`. |
| `Country` | string | Country (or countries) of operation. |
| `Active` | string | `Y` or `N` — whether the utility is currently operating. |

## substations.csv / substations_clean.csv

| Column | Type | Description |
|---|---|---|
| `Substation ID` | int64 | Unique integer identifier. Primary key. |
| `Name` | string | Full substation name (e.g. "Achimota Substation"). This is the value that appears in `lines.csv`'s `Source Substation`/`Destination Substation` columns — **not** `Short Name`. |
| `Short Name` | string | Place name only (e.g. "Achimota"), used for labelling on maps/graphs. |
| `Region` | string | Administrative region, or bordering country for cross-border nodes. |
| `Country` | string | Country. |
| `Latitude` | float64 | Approximate decimal-degree latitude. |
| `Longitude` | float64 | Approximate decimal-degree longitude. |
| `Voltage (kV)` | int64 | Nominal operating voltage: one of 11, 33, 69, 161, 330. |
| `Capacity (MVA)` | float64 | Rated capacity in megavolt-amperes. |
| `Commissioning Year` | int64 | Year the substation was notionally commissioned. |
| `Type` | string | One of `Distribution`, `Bulk Supply Point`, `Transmission`. |
| `Status` | string | `Active` or `Inactive`. |

## lines.csv / lines_clean.csv

| Column | Type | Description |
|---|---|---|
| `Line ID` | int64 | Unique integer identifier. Primary key. |
| `Utility ID` | int64 | Foreign key -> `utilities.Utility ID`. Which utility owns/operates the line. |
| `Source Substation ID` | int64 | Foreign key -> `substations.Substation ID`. One end of the line. |
| `Source Substation` | string | Denormalised copy of the source substation's `Name`, kept for readability — always re-derive from the ID for anything programmatic. |
| `Destination Substation ID` | int64 | Foreign key -> `substations.Substation ID`. The other end of the line. |
| `Destination Substation` | string | Denormalised copy of the destination substation's `Name`. |
| `Voltage (kV)` | int64 | Operating voltage of the line. |
| `Length (km)` | float64 | Approximate line length, derived from source/destination coordinates via the haversine formula. |
| `Capacity (MVA)` | float64 | Rated transfer capacity. |
| `Status` | string | `Active` or `Under Maintenance`. |
| `Line Type` | string | `Overhead` or `Underground`. |

## data/integrated/master_dataset.csv (Task 1.3 output)

One row per line, widened with the full record of both endpoint substations
and the operating utility. Column naming: line columns are unprefixed;
substation columns are prefixed `Source ` / `Destination `; utility columns
are prefixed `Utility `.

| Column pattern | Source table | Example |
|---|---|---|
| `Line ID`, `Voltage (kV)`, `Length (km)`, `Capacity (MVA)`, `Status`, `Line Type` | `lines` | `Length (km)` = 25.2 |
| `Source Substation ID`, `Source Name`, `Source Short Name`, `Source Region`, `Source Country`, `Source Latitude`, `Source Longitude`, `Source Voltage (kV)`, `Source Capacity (MVA)`, `Source Commissioning Year`, `Source Type`, `Source Status` | `substations` (joined on `Source Substation ID`) | `Source Region` = "Greater Accra" |
| `Destination Substation ID`, `Destination Name`, ... (same fields as Source) | `substations` (joined on `Destination Substation ID`) | `Destination Region` = "Greater Accra" |
| `Utility ID`, `Utility Name`, `Utility Alias`, `Utility Code`, `Utility Type`, `Utility Country`, `Utility Active` | `utilities` (joined on `Utility ID`) | `Utility Alias` = "GRIDCo" |

Note the `Voltage (kV)` and `Capacity (MVA)` fields exist on **both** `lines`
and `substations` with the same name but different meanings (line rating vs.
substation rating) — after the join these are disambiguated as
`Voltage (kV)` (the line's own rating, left unprefixed) vs.
`Source Voltage (kV)` / `Destination Voltage (kV)` (the endpoint substations'
ratings).

## Lookup dictionaries (Task 1.3 output)

For O(1) ID -> record lookups (used by later tasks and by GridCare-Lite's
substation import), Task 1.3 also serialises:

- `data/integrated/substations_lookup.json` — `{substation_id: {name, short_name, region, country, voltage_kv, capacity_mva, commissioning_year, type, status}}`
- `data/integrated/utilities_lookup.json` — `{utility_id: {name, alias, code, type, country, active}}`
