# Group2-CS-project

CS 112 Summer 2026 Final Course Project — an integrated data science and software
engineering project with three components:

1. **[grid-analysis/](grid-analysis/)** — National Electricity Grid Network Analysis
   (data cleaning, EDA, NetworkX graph modelling, N-1 contingency analysis, geospatial
   visualisation).
2. **[gridcare-lite/](gridcare-lite/)** — GridCare-Lite, a Tkinter/SQLite outage and
   maintenance management system for a utility's field operations team.
3. **[cliniccare-lite/](cliniccare-lite/)** — ClinicCare-Lite, a Flask/JSON clinic
   patient administration and communication system (strictly administrative — no
   diagnosis, symptom interpretation, or treatment recommendation).

## Getting started

Each component has its own `README.md` and `requirements.txt`. General pattern:

```bash
cd <component>
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

See each component's README for how to run it.

## Team

Four GitHub collaborators on this repo. Role split below is proposed from the
course spec's suggested breakdown (data engineer, data analyst, visualisation
specialist, software engineer) — confirm/reassign with the team and replace
the `_proposed_` tags once agreed.

- [@josiahaggrey](https://github.com/josiahaggrey) — _proposed: Data analysis / business intelligence / ClinicCare-Lite patient services_
- [@braimahhariz](https://github.com/braimahhariz) — _proposed: Data engineering / network analysis / GridCare-Lite architecture_ (author of `grid-analysis` Tasks 1.1-1.3 and the current `gridcare-lite` implementation)
- [@CoulNibo](https://github.com/CoulNibo) — _proposed: Visualisation / dashboards / ClinicCare-Lite clinician services_
- [@Cl-Mado](https://github.com/Cl-Mado) — _proposed: Software engineering / GridCare-Lite GUI / ClinicCare-Lite UI & testing_

See [docs/architecture.md](docs/architecture.md) for how the three components
fit together and [docs/coding_standards.md](docs/coding_standards.md) for the
conventions to follow.

## Project boundaries

ClinicCare-Lite is an **administrative and communication system only**. It must never
diagnose patients, interpret symptoms, calculate disease risk, recommend treatment, or
prescribe medication. Automated features are limited to structural/non-clinical checks
(e.g. "is this required field present?").
