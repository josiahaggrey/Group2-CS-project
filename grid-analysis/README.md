# National Electricity Grid Network Analysis

Data science component: cleans and analyses a synthetic Ghana-grounded electricity
grid dataset (utilities, substations, transmission/distribution lines), models it as
a graph with NetworkX, and runs a simplified N-1 contingency analysis.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Generate the seeded dataset (identical for every team member, `random.seed(42)`):

   ```bash
   python generate_dataset.py
   ```

   Writes `data/utilities.csv`, `data/substations.csv`, `data/lines.csv`.

2. Run Task 1.1 - data cleaning and preprocessing:

   ```bash
   python tasks/task_1_1_data_cleaning.py
   ```

   Writes `data/cleaned/utilities_clean.csv`, `data/cleaned/substations_clean.csv`,
   `data/cleaned/lines_clean.csv`, and `reports/task_1_1_data_cleaning_report.md`
   (missing-value strategy, transformations applied, duplicate/relationship/
   coordinate-bounds checks, and a basic statistics summary). Every downstream
   task should read from `data/cleaned/`, not the raw files.

3. Run Task 1.2 - exploratory data analysis:

   ```bash
   python tasks/task_1_2_eda.py
   ```

   Reads from `data/cleaned/`. Writes `reports/task_1_2_eda_report.md` (descriptive
   stats, categorical frequency distributions, top utilities by line count,
   most-connected substations, capacity distribution, infrastructure age by
   region, line status proportions, initial hypotheses, and patterns for further
   investigation) plus the supporting charts under `reports/figures/task_1_2/`.

4. Run Task 1.3 - data integration and relationship mapping:

   ```bash
   python tasks/task_1_3_data_integration.py
   ```

   Reads from `data/cleaned/`. Drops any orphaned lines (a foreign key that
   doesn't resolve), then joins lines with both endpoint substations and the
   operating utility into a single wide table. Writes
   `data/integrated/master_dataset.csv`, `data/integrated/substations_lookup.json`,
   `data/integrated/utilities_lookup.json`, and
   `reports/task_1_3_data_integration_report.md` (FK relationships, orphan
   handling, join validation, lookup sizes, and a preview). See also
   [`docs/entity_relationship_diagram.md`](docs/entity_relationship_diagram.md)
   and [`docs/data_dictionary.md`](docs/data_dictionary.md).

5. Run the combined starter analysis (inspection, cleaning, EDA, merging, network
   analysis, N-1 contingency check — a rougher, all-in-one pass through Part B
   Tasks 1-5 of the spec):

   ```bash
   python analysis_starter.py
   ```

   Writes `data/eda_regions.png`, `data/eda_top_substations.png`,
   `data/network_graph.png`, `data/merged_lines.csv`.

6. Optional: build the interactive map (requires `folium`) by calling
   `create_grid_map(substations, lines)` from `analysis_starter.py`, or add it to
   `main()`.

## Testing

```bash
pip install pytest
pytest
```

`tests/` covers Tasks 1.1-1.3: unit tests against small synthetic DataFrames
for each function's logic (does `validate_relationships` actually catch a bad
foreign key? does `find_and_handle_orphans` drop only the orphan?), plus
integration tests that run the real scripts end-to-end via the `pipeline`
fixture and check the actual output files (row counts, no dangling foreign
keys, no missing values, reproducibility across re-runs, valid/complete
lookup JSON). 40 tests, all passing as of the last run.

## Task progress (Part A of the spec)

- [x] **Task 1.1** — Data Cleaning and Preprocessing (`tasks/task_1_1_data_cleaning.py`)
- [x] **Task 1.2** — Exploratory Data Analysis (`tasks/task_1_2_eda.py`)
- [x] **Task 1.3** — Data Integration and Relationship Mapping (`tasks/task_1_3_data_integration.py`)
- [ ] Task 2.1 — Network Analysis
- [ ] Task 2.2 — Geographic and Geospatial Analysis
- [ ] Task 2.3 — Business Intelligence and Reliability Analysis
- [ ] Task 3.1 — Comprehensive Dashboard Development
- [ ] Task 3.2 — Advanced Visualisations and Insights
- [ ] Task 3.3 — Documentation and Presentation

`analysis_starter.py` is a rough, ungraded pass through the equivalent Part B
tasks and is useful as a reference, but the `tasks/task_N_N_*.py` scripts are
the actual per-task deliverables the rubric expects.
