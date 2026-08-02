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

Four-member team split across the components — see the course project spec for the
suggested role breakdown (data engineer, data analyst, visualisation specialist,
software engineer) and grading rubric. Update this section with your team's actual
member names and role assignments.

- Member 1: _Data engineering / network analysis / GridCare-Lite architecture_
- Member 2: _Data analysis / business intelligence / ClinicCare-Lite patient services_
- Member 3: _Visualisation / dashboards / ClinicCare-Lite clinician services_
- Member 4: _Software engineering / GridCare-Lite GUI / ClinicCare-Lite UI & testing_

## Project boundaries

ClinicCare-Lite is an **administrative and communication system only**. It must never
diagnose patients, interpret symptoms, calculate disease risk, recommend treatment, or
prescribe medication. Automated features are limited to structural/non-clinical checks
(e.g. "is this required field present?").
