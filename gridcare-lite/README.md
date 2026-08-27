# GridCare-Lite

A Tkinter + SQLite outage and maintenance management system prototype for a utility's
field operations team, with role-based access for administrator, engineer,
technician, and customer-service users.

## Design

The GUI (`app.py`) never writes raw SQL. All data and behaviour live in
domain classes in `models.py`:

- **`User`** — authentication (`User.authenticate()`), role lookup
  (`User.find_by_role()`), bcrypt password hashing.
- **`Substation`** — reference data imported from the grid-analysis
  component (`Substation.import_from_csv()`); `regions()` and `exists()`
  back the dashboard's region filter and outage-reporting validation.
- **`Outage`** — reported faults (with a `severity`: Low/Medium/High/Critical),
  moving `Open -> In Progress -> Resolved` via `mark_in_progress()` /
  `mark_resolved()`. `report()` rejects a nonexistent substation and an
  exact duplicate still open at the same substation. `search()` filters by
  region/status for the dashboard.
- **`WorkOrder`** — technician assignment and scheduling. `WorkOrder.assign()`
  also moves its outage to "In Progress"; `mark_complete()` also resolves it -
  the state-transition rule lives in one place, not duplicated across screens.
- **`Complaint`** — customer complaints, optionally linked to an outage
  (validated to exist before linking); `all()` lists every complaint logged
  so far, newest first.
- **`Report`** — read-only aggregate queries for the Reports screen: status
  counts, severity counts, outages by region, and average resolution time.
  Never mutates data - only summarises what the other classes have recorded.

Every class defines `__str__` so an instance is directly usable as a combobox
label or dashboard row without the GUI reaching into its fields. Screens in
`app.py` only handle layout/input and call these methods - e.g.
`NewOutageForm` calls `Outage.report(...)`, it doesn't build the `INSERT`
itself. `db.py` owns only the schema (`init_db()`, plus a small
`_add_column_if_missing()` migration helper), not query logic.

Every screen method that touches the database is wrapped with
`app.py`'s `@guard_db_errors` decorator, which catches `sqlite3.Error` and
shows one friendly dialog instead of letting the exception crash the app.

Visual styling is factored out into `theme.py` (colour/font tokens plus one
`configure_style()` call, and a small dependency-free `draw_horizontal_bars()`
canvas chart for the Reports screen) so presentation stays separate from the
screens' logic - the same domain/presentation split as `models.py` vs `app.py`.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Initialise the database:

   ```bash
   python db.py
   ```

   Safe to re-run on an existing `gridcare.db` from before the `severity`
   column existed - `_add_column_if_missing()` migrates it in place instead
   of erroring.

2. Seed demo accounts:

   ```bash
   python seed_users.py
   ```

   Creates `admin1`, `engineer1`, `tech1`, `cs1` (see `seed_users.py` for passwords).
   Safe to re-run - `User.find_by_username()` is checked before creating.

3. Run the app:

   ```bash
   python app.py
   ```

   `app.py`'s `ensure_substations_loaded()` automatically imports
   `../grid-analysis/data/cleaned/substations_clean.csv` on first run (skipped
   if the `substations` table already has rows, so it's a no-op on every run
   after the first). If you've only cloned `gridcare-lite` on its own without
   `grid-analysis` alongside it, this is skipped with a console message
   instead of crashing — the app still runs, just with an empty substation
   picker until you import data manually via `Substation.import_from_csv()`.

4. Run the tests:

   ```bash
   pytest
   ```

   35 tests against a fresh in-memory database per test - see
   `docs/test_plan.md` for which spec-required cases each one covers.

## What's implemented

- Automatic substation reference-data import on first run (see Usage step 3)
  - no more empty picker on a fresh clone.
- Login with bcrypt-hashed passwords, role-based dashboard routing.
- Log Out (dashboard header) — returns to the login screen without
  restarting the app; a fresh `LoginWindow` is rebuilt against the same
  open `conn`, so no data is lost or re-read from disk.
- A consistent visual theme (`theme.py`): slate header bar with the current
  user/role, amber primary-action buttons, bordered cards for the login and
  popup forms, and striped Treeview rows - applied once via
  `configure_style()`, not per-screen.
- Outage dashboard (all roles) with live refresh, region + status filters,
  and a severity column.
- Log new outage (engineer/admin) against a substation, with a severity
  (Low/Medium/High/Critical). Rejected if the substation doesn't exist or an
  identical description is already open at that substation.
- Assign work order to a technician (admin) — moves the outage to "In Progress".
- Technician view of assigned work orders, with "mark complete" (moves outage to
  "Resolved").
- Customer complaint logging (customer-service), optionally linked to an outage ID,
  with validation that the outage exists.
- **View Complaints** (customer-service, admin) — the complaint history that
  logging alone didn't provide before.
- **Reports** (admin) — total/open/in-progress/resolved/complaint counts,
  average resolution time, and simple bar charts of outages by region and
  by severity. No matplotlib dependency - `theme.py`'s
  `draw_horizontal_bars()` draws directly on a `tk.Canvas`.
- Every DB-touching screen method is wrapped with `@guard_db_errors` -  a
  locked/unreachable database shows a dialog, not a crash.
- 35 automated tests (`pytest`) covering `models.py`: validation, state
  transitions, filters, and the Report aggregates, against a fresh
  in-memory SQLite database per test.

## What's left (see course spec Week 3–5 tasks)

- Status-history tracking table (an audit trail of status changes over
  time - currently a status change overwrites in place).
- A field to record *what was done* when a technician marks a work order
  complete (currently just a status flip, no notes).
- Registration screen (currently accounts are seeded directly).
- A user guide walkthrough per role, and a recorded demo video (both
  explicit spec deliverables, still outstanding).
- Simple charts for the Reports screen currently use a lightweight
  hand-rolled canvas bar chart; consider matplotlib-in-Tkinter if richer
  visuals are wanted later.
