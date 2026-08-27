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
  component (`Substation.import_from_csv()`).
- **`Outage`** — reported faults, moving `Open -> In Progress -> Resolved`
  via `mark_in_progress()` / `mark_resolved()`.
- **`WorkOrder`** — technician assignment and scheduling. `WorkOrder.assign()`
  also moves its outage to "In Progress"; `mark_complete()` also resolves it -
  the state-transition rule lives in one place, not duplicated across screens.
- **`Complaint`** — customer complaints, optionally linked to an outage
  (validated to exist before linking).

Every class defines `__str__` so an instance is directly usable as a combobox
label or dashboard row without the GUI reaching into its fields. Screens in
`app.py` only handle layout/input and call these methods - e.g.
`NewOutageForm` calls `Outage.report(...)`, it doesn't build the `INSERT`
itself. `db.py` owns only the schema (`init_db()`), not query logic.

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

## What's implemented

- Automatic substation reference-data import on first run (see Usage step 3)
  - no more empty picker on a fresh clone.
- Login with bcrypt-hashed passwords, role-based dashboard routing.
- Outage dashboard (all roles) with live refresh.
- Log new outage (engineer/admin) against a substation.
- Assign work order to a technician (admin) — moves the outage to "In Progress".
- Technician view of assigned work orders, with "mark complete" (moves outage to
  "Resolved").
- Customer complaint logging (customer-service), optionally linked to an outage ID,
  with validation that the outage exists.
- Full domain layer (`models.py`) covered by manual end-to-end verification:
  report → assign → complete → resolved, wrong-password rejection, empty-description
  and nonexistent-outage-ID validation errors.

## What's left (see course spec Week 3–5 tasks)

- Automated tests for `models.py` (mirroring the grid-analysis `tests/` approach:
  unit tests per class against a temp SQLite DB, plus an end-to-end workflow test).
- Status-history tracking table, richer reporting/dashboard view (open outage counts,
  average resolution time, outages by region).
- More thorough input validation and negative-path testing (invalid dates, duplicate
  entries, database failures).
- Registration screen (currently accounts are seeded directly).
- Entity-relationship diagram and data dictionary for the final report.
