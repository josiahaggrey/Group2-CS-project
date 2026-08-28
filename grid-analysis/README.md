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

7. Run the Task 3.1 dashboard:

   ```bash
   streamlit run dashboard.py
   ```

   Reads from `data/cleaned/` (so run steps 1-2 at least once first). Opens
   an interactive Streamlit app at `http://localhost:8501` with five tabs -
   see "Task 3.1: Dashboard" below.

## Design (Tasks 1.1-1.3)

`tasks/task_1_1_data_cleaning.py`, `task_1_2_eda.py`, and
`task_1_3_data_integration.py` are all written as small class hierarchies
rather than top-level functions:

- **Task 1.1**: `DatasetCleaner` is a base class implementing the cleaning
  pipeline once as a template method (`clean()`: standardise missing values
  -> coerce dtypes -> drop rows missing their key -> find duplicate keys ->
  impute categoricals -> drop duplicate rows). `UtilitiesCleaner`,
  `SubstationsCleaner`, and `LinesCleaner` subclass it, each only declaring
  *what* to clean (key column, numeric/ID columns, imputation strategy) via
  class attributes - `SubstationsCleaner` additionally adds
  `check_coordinate_bounds()`, since only substations have coordinates.
  `RelationshipValidator` and `CleaningReportBuilder` are separate classes
  with one responsibility each, composed together by the `DataCleaningPipeline`
  orchestrator.
- **Task 1.2**: `GridEDAAnalyzer` wraps the three cleaned DataFrames and
  exposes one method per EDA question from the spec. `ChartGenerator` only
  knows how to render/save a bar chart or histogram - it never touches the
  domain data. `EDAReportBuilder` composes an analyzer + a chart generator
  into the markdown report; `EDAPipeline` is the entry point.
- **Task 1.3**: `OrphanHandler`, `DatasetIntegrator`, and `LookupBuilder`
  each own one responsibility (drop unresolvable foreign keys; build+validate
  the join; serialise ID->record lookups), so each is independently testable.
  `IntegrationReportBuilder` turns their results into markdown;
  `DataIntegrationPipeline` is the entry point.

Every orchestrator class (`DataCleaningPipeline`, `EDAPipeline`,
`DataIntegrationPipeline`) contains no data-transformation logic of its own -
only wiring - so the actual logic lives in small, single-responsibility
classes that unit tests can instantiate directly with synthetic data.

## Task 3.1: Dashboard

`dashboard.py` is a single-file Streamlit app matching the spec's required
tab structure exactly:

- **Overview** — executive-summary metric tiles (substation/line/utility
  counts, total capacity, % lines active, network density) plus regional
  and voltage-level distribution charts.
- **Network** — region-filterable force-directed graph (node size = degree
  centrality, colour = voltage), a top-10 centrality table, and an
  interactive **N-1 contingency check**: pick any substation, see the
  connected-component count before/after removing it.
- **Geography** — a Plotly `Scattergeo` map of every substation (sized by
  capacity, coloured by voltage) with lines drawn between connected pairs
  (green = Active, amber = Under Maintenance), filterable by region,
  voltage, and utility.
- **Reliability** — utility footprint, line-status breakdown, asset-age
  histogram, capacity distribution by voltage tier, and the regions with
  the fewest substations.
- **Search** — a substation finder (region/voltage/capacity/connections/
  centrality rank) and a multi-utility comparison table/chart.

**Design note - what this dashboard does *not* build on:** Tasks 2.1-2.3
(the standalone network-analysis, geospatial, and business-intelligence
scripts+reports) haven't been produced as separate deliverables yet - see
the checklist below. Rather than block the dashboard on those, Task 3.1
computes everything it needs directly with NetworkX/pandas on the cleaned
Task 1.1-1.3 data. That satisfies the dashboard's own requirement ("a
fully functional interactive dashboard integrating all analyses") but the
individual Task 2.1/2.2/2.3 write-ups (a dedicated report per task,
matching the format Tasks 1.1-1.3 already have) are still outstanding and
worth doing for the record, even though their analysis now also exists
inside `dashboard.py`.

Uses only Plotly for every chart/map (matching the course spec's own
Task 3.1 sample code, which imports `streamlit`, `plotly.express`, and
`plotly.graph_objects` - not `folium`), so no `streamlit-folium` dependency
is needed to run it.

## Testing

```bash
pip install pytest
pytest
```

`tests/` covers Tasks 1.1-1.3: unit tests that instantiate the classes above
directly against small synthetic DataFrames (does `RelationshipValidator`
actually catch a bad foreign key? does `OrphanHandler` drop only the orphan?),
plus integration tests that run the real scripts end-to-end via the
`pipeline` fixture and check the actual output files (row counts, no
dangling foreign keys, no missing values, reproducibility across re-runs,
valid/complete lookup JSON). 47 tests, all passing as of the last run.

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
