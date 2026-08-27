# System Architecture

Three independent components share one repository and one dataset lineage.
Nothing shares a database or a running process — the only coupling is that
`grid-analysis` produces the substation reference data that `gridcare-lite`
imports.

```mermaid
flowchart LR
    subgraph DS["grid-analysis (data science)"]
        GEN["generate_dataset.py"] --> RAW[("utilities.csv\nsubstations.csv\nlines.csv")]
        RAW --> T11["Task 1.1\ncleaning"]
        T11 --> CLEAN[("data/cleaned/*.csv")]
        CLEAN --> T12["Task 1.2\nEDA"]
        CLEAN --> T13["Task 1.3\nintegration"]
        T13 --> MASTER[("data/integrated/\nmaster_dataset.csv")]
    end

    subgraph GC["gridcare-lite (Tkinter + SQLite)"]
        GCDB[("gridcare.db")]
        GCMODELS["models.py\nUser / Substation / Outage /\nWorkOrder / Complaint"]
        GCAPP["app.py (Tkinter GUI)"]
        GCMODELS --> GCDB
        GCAPP --> GCMODELS
    end

    subgraph CC["cliniccare-lite (Flask + JSON)"]
        CCJSON[("data/*.json")]
        CCMODELS["models/\nUser / Clinic / HealthTask /\nTaskSubmission / Message"]
        CCAPP["app.py (Flask routes)"]
        CCMODELS --> CCJSON
        CCAPP --> CCMODELS
    end

    CLEAN -. "Substation.import_from_csv()" .-> GCDB

    style DS fill:#1f2937,color:#fff,stroke:#4b5563
    style GC fill:#1f2937,color:#fff,stroke:#4b5563
    style CC fill:#1f2937,color:#fff,stroke:#4b5563
```

## Why this shape

- **No shared runtime.** `grid-analysis` is a batch pipeline (scripts + a
  pytest suite), `gridcare-lite` is a desktop app, `cliniccare-lite` is a web
  app. They can be developed, tested, and demoed independently — a bug in one
  never blocks the other two.
- **One directional data dependency.** `gridcare-lite` optionally imports
  `grid-analysis`'s cleaned substation list so outages can only be logged
  against a real substation (`Substation.import_from_csv`, see
  `gridcare-lite/README.md`). Nothing flows the other way, and
  `cliniccare-lite` has no dependency on either.
- **Each app owns its persistence.** SQLite for `gridcare-lite` (relational:
  outages reference substations and technicians by ID, work orders reference
  outages), JSON files for `cliniccare-lite` (document-shaped: a submission
  or message is naturally a single record, not a joined row).
- **The GUI layer never touches storage directly.** Both apps route every
  read/write through a domain class (`gridcare-lite/models.py`,
  `cliniccare-lite/models/*.py`) — screens/routes only handle input and
  layout. See each component's `docs/class_diagram.md`.

## Component docs

- [grid-analysis/docs/entity_relationship_diagram.md](../grid-analysis/docs/entity_relationship_diagram.md)
  and [data_dictionary.md](../grid-analysis/docs/data_dictionary.md)
- [gridcare-lite/docs/class_diagram.md](../gridcare-lite/docs/class_diagram.md),
  [use_case_diagram.md](../gridcare-lite/docs/use_case_diagram.md),
  [er_diagram.md](../gridcare-lite/docs/er_diagram.md)
- [cliniccare-lite/docs/class_diagram.md](../cliniccare-lite/docs/class_diagram.md),
  [use_case_diagram.md](../cliniccare-lite/docs/use_case_diagram.md)
