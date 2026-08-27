# Coding & Documentation Standards

These are the conventions the codebase already follows (extracted from
`grid-analysis/tasks/`, `gridcare-lite/models.py`, and
`cliniccare-lite/models/`) — write new code to match, don't introduce a
second style.

## Python style

- **Naming:** `snake_case` for functions/variables/modules, `PascalCase` for
  classes, `UPPER_SNAKE_CASE` for constants (e.g. `VALID_ROLES`,
  `REVIEW_OUTCOMES`).
- **One domain concept per class, and the class owns its own persistence.**
  A model class both holds data (`__init__`) and defines the operations that
  read/write it (classmethods/staticmethods calling the DB or JSON store).
  Screens and Flask routes never write raw SQL or touch a JSON file
  directly — see `docs/architecture.md`.
- **Validation raises, callers catch.** Model methods raise `ValueError` (or
  `KeyError` for "not found") with a message fit to show a user directly;
  GUI/route code wraps the call and displays `str(error)`. Don't return
  `None`/`False` for a validation failure when a message is needed.
- **`__str__` on every display-facing class** (see `gridcare-lite/models.py`)
  so an instance is directly usable as a combobox label or list row without
  the caller reaching into its fields.
- **Docstrings explain *why*, not *what*.** A class/module docstring is
  worth writing when it records a non-obvious constraint or design decision
  (e.g. `models.py`'s note on why state transitions live on one class, or
  `json_store.py`'s note on the `truncate()` fix). Don't restate what a
  well-named method obviously does.
- **No comments narrating the diff.** Comments describe the code as it is,
  not "added for Task 1.3" or "fixed bug from last review" — that belongs in
  the commit message.

## Testing

- **pytest**, one test file per task/module:
  `tests/test_task_1_1_data_cleaning.py` mirrors
  `tasks/task_1_1_data_cleaning.py`. Follow this pairing for new modules in
  `gridcare-lite` and `cliniccare-lite`.
- Cover both the success path and the documented negative cases (see each
  component's `docs/test_plan.md`).
- `grid-analysis/conftest.py` shows the pattern for shared fixtures (e.g. a
  temp copy of the dataset) — reuse it rather than duplicating setup.

## Documentation layout

- `<component>/README.md` — what it is, how to run it, what's implemented,
  what's left. Keep "what's implemented" and "what's left" current as you
  merge features; a stale README is worse than none.
- `<component>/docs/` — diagrams and design records (class diagram, use-case
  diagram, ER diagram, test plan). One file per artifact, named for what it
  contains.
- `<component>/reports/` — generated, dated output (e.g.
  `grid-analysis/reports/task_1_1_data_cleaning_report.md`) — reproducible
  from the code, not hand-maintained.

## Git workflow

- **Commit messages:** imperative mood, present tense, no trailing period —
  `Add Task 1.3: data integration and relationship mapping`, not `Added...`
  or `Adding...`. State what the commit does, not a diff summary.
- **One logical change per commit.** The existing history (one commit per
  task/feature) is the model to follow.
- **Branch per feature/task**, merge into `main` via PR once a feature works
  end-to-end. `main` should always be in a demoable state.
- Don't commit generated artifacts that aren't meant to be reproducible
  records (`__pycache__/`, `.pytest_cache/` — check `.gitignore` covers
  these; add missing patterns rather than committing the files).

## Security-sensitive code

- Passwords are always hashed with `bcrypt` before storage — never compared
  or stored in plaintext (see `gridcare-lite/models.py: User.hash_password`
  and `cliniccare-lite/models/user.py`).
- File uploads are validated (extension, size) **before** touching the
  filesystem (`cliniccare-lite/models/task_submission.py:
  TaskSubmission.validate_file`).
- Secrets (`CLINICCARE_SECRET_KEY`, `EMAIL_ADDRESS`/`EMAIL_PASSWORD`) are
  read from environment variables, never hard-coded — see each component's
  README for the dev-only fallback behaviour.
