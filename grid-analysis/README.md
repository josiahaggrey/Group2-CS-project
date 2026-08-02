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

2. Run the starter analysis (inspection, cleaning, EDA, merging, network analysis,
   N-1 contingency check):

   ```bash
   python analysis_starter.py
   ```

   Writes `data/eda_regions.png`, `data/eda_top_substations.png`,
   `data/network_graph.png`, `data/merged_lines.csv`.

3. Optional: build the interactive map (requires `folium`) by calling
   `create_grid_map(substations, lines)` from `analysis_starter.py`, or add it to
   `main()`.

## Next steps

Split `analysis_starter.py`'s tasks into a Jupyter notebook per the project's Week 1–3
task breakdown (EDA, business intelligence, geospatial analysis, dashboard) — see the
course spec for the full task list, deliverables, and evaluation criteria.
