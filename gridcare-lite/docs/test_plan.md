# Test Plan — GridCare-Lite

Per the course spec's Section 7 test documentation format (objective /
input / expected outcome / actual outcome / pass-fail / defect /
corrective action / retest). Originally written in Week 1 as a planning
artifact with everything "not yet executed"; `tests/` (`pytest`, 38 tests)
now automates every case below except GC-03 and GC-14, which are GUI-level
and still need manual/UI-test coverage.

| ID | Objective | Input | Expected outcome | Status |
|---|---|---|---|---|
| GC-01 | Reject an invalid login | Wrong password for an existing username | `messagebox.showerror("Login Failed", ...)`; no dashboard shown | Automated — `test_authenticate_rejects_wrong_password` |
| GC-02 | Reject login for a nonexistent user | Username not in `users` table | Same as GC-01 | Automated — `test_authenticate_rejects_nonexistent_user` |
| GC-03 | Role-access: engineer cannot assign work orders | Log in as `engineer1`, inspect dashboard buttons | "Assign Work Order" button absent | Manually verified (GUI) — see Known Gaps: still GUI-only enforcement |
| GC-04 | Role-access: technician sees only their own work orders | Log in as `tech1` with work orders assigned to a different technician also in the DB | `WorkOrder.for_technician` returns only rows for the logged-in technician | Automated — `test_for_technician_scoped_to_that_technician` |
| GC-05 | Reject an outage with an empty description | `Outage.report(conn, sub_id, user_id, "")` | Raises `ValueError` | Automated — `test_report_rejects_empty_description` |
| GC-06 | Reject an outage against a nonexistent substation | `Outage.report(conn, 9999, user_id, "desc")` | Raises `ValueError` | **Fixed & automated** — `test_report_rejects_nonexistent_substation` |
| GC-07 | Assigning a work order moves its outage to "In Progress" | `WorkOrder.assign(conn, outage_id, tech_id, "2026-09-01")` | `Outage.status == "In Progress"` after assign | Automated — `test_assign_moves_outage_to_in_progress` |
| GC-08 | Reject a work order with no scheduled date | `WorkOrder.assign(conn, outage_id, tech_id, "")` | Raises `ValueError` | Automated — `test_assign_rejects_missing_scheduled_date` |
| GC-09 | Completing a work order resolves its outage | `WorkOrder.mark_complete(conn)` | Work order status "Completed"; linked outage status "Resolved" with `resolved_at` set | Automated — `test_mark_complete_resolves_the_outage` |
| GC-10 | Duplicate outage records | Submit the same description against the same substation twice, while the first is still open | Raises `ValueError`; allowed again once the first is resolved | **Fixed & automated** — `test_report_rejects_exact_duplicate_while_open`, `test_report_allows_same_description_once_resolved` |
| GC-11 | Reject a complaint linked to a nonexistent outage | `Complaint.log(conn, user_id, "name", "desc", outage_id=9999)` | Raises `ValueError` | Automated — `test_log_rejects_nonexistent_outage_id` |
| GC-12 | Reject a complaint with no customer name / description | `Complaint.log(conn, user_id, "", "desc")` | Raises `ValueError` | Automated — `test_log_rejects_missing_name`, `test_log_rejects_missing_description` |
| GC-13 | Database/connection failure is handled gracefully | Simulate a locked/unreachable `gridcare.db` | App shows an error dialog rather than crashing | **Fixed & automated** — `app.guard_db_errors` wraps every DB-touching screen method; `tests/test_app.py::test_guard_db_errors_catches_sqlite_error_instead_of_raising` |
| GC-14 | Report accuracy: dashboard reflects current DB state | Insert an outage directly in SQLite, click "Refresh" | New row appears without restarting the app | Manually verified (GUI) — not practical to automate without a GUI test harness |
| GC-15 | Password hashing | Inspect `users.password_hash` after `User.create(...)` | Value is a bcrypt hash, never the plaintext password | Automated — `test_create_hashes_password_not_plaintext` |

## New coverage beyond the original 15 cases

Added alongside the severity field, dashboard filters, Reports screen, and
Complaints view:

| Area | What's tested |
|---|---|
| Severity | Valid values accepted, invalid value rejected, defaults to "Medium" when omitted |
| Filters | `Outage.search()` by region alone, status alone, both, and neither |
| Substation reference data | CSV import creates rows, re-import is idempotent (`INSERT OR IGNORE`), `exists()`, `regions()` |
| Report aggregates | Zero-filled status/severity counts on an empty DB, real counts, `average_resolution_hours` both when nothing is resolved (`None`) and when something is, `outages_by_region` grouping, `summary()`'s combined shape |
| Complaint history | `Complaint.all()` returns newest-first (with a `complaint_id` tiebreaker for complaints logged in the same second — see below), includes the logging user's username |

## Known gaps still open

- **GC-03:** role checks still live only in which buttons `app.py` builds.
  The spec explicitly requires role separation to be enforced by
  "application logic and database permissions" too — worth adding a
  role check inside the model methods that matter most (`WorkOrder.assign`,
  `Outage.mark_resolved`) so a modified/malicious client can't bypass the
  GUI. Not automated, since it's about what a compromised/nonstandard
  client could do, not what the shipped GUI does.
- **GC-14:** dashboard live-refresh is GUI behaviour (a Treeview repopulating
  on a button click) that isn't practical to unit-test against `models.py`
  alone — would need a GUI-level test harness (e.g. driving Tkinter events),
  which the project doesn't have yet.
- No status-history audit trail — a status change overwrites in place, so
  "when did this move from Open to In Progress" isn't recorded (see
  README's "What's left").

## Defect found and fixed during test-writing

Writing `test_all_returns_newest_first_with_logger_username` caught a real
ordering bug: `Complaint.all()` ordered by `logged_at DESC` only, and
SQLite's `CURRENT_TIMESTAMP` has 1-second resolution - two complaints
logged within the same second had no defined relative order. Fixed by
adding `complaint_id DESC` as a tiebreaker (and applied the same fix to
`Outage.all()`/`Outage.search()`, which had the identical issue). This is
exactly the kind of defect this test plan exists to catch: it never
would have surfaced from manual clicking, only from an automated test
run twice in a row.

## Automated coverage

`tests/test_models.py` (35 tests) + `tests/test_app.py` (3 tests, covering
`guard_db_errors`) + `tests/conftest.py` (fixtures: a fresh in-memory DB per
test via the real `db.init_db()`, one substation, one user per role) —
mirrors the pattern in `grid-analysis/tests/conftest.py`. 38 tests total.
Run with `pytest` from the `gridcare-lite/` directory.
