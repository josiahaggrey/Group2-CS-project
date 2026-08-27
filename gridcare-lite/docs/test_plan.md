# Initial Test Plan — GridCare-Lite

Planning artifact for Week 1, per the course spec's Section 7 test
documentation format (objective / input / expected outcome / actual outcome
/ pass-fail / defect / corrective action / retest). Execution happens
incrementally as each feature lands and formally in Week 4; this table
tracks planned coverage. **Status** distinguishes what `gridcare-lite/README.md`
explicitly claims was manually verified (report → assign → complete →
resolved, wrong-password rejection, empty-description and
nonexistent-outage-ID validation errors) from everything else, which is
implemented but not yet confirmed by any test, automated or manual.

| ID | Objective | Input | Expected outcome | Status |
|---|---|---|---|---|
| GC-01 | Reject an invalid login | Wrong password for an existing username | `messagebox.showerror("Login Failed", ...)`; no dashboard shown | Manually verified (per README) |
| GC-02 | Reject login for a nonexistent user | Username not in `users` table | Same as GC-01 | Not yet executed |
| GC-03 | Role-access: engineer cannot assign work orders | Log in as `engineer1`, inspect dashboard buttons | "Assign Work Order" button absent | Not yet executed — see Known Gaps (GUI-only enforcement) |
| GC-04 | Role-access: technician sees only their own work orders | Log in as `tech1` with work orders assigned to a different technician also in the DB | `WorkOrder.for_technician` returns only rows for the logged-in technician | Not yet executed |
| GC-05 | Reject an outage with an empty description | `Outage.report(conn, sub_id, user_id, "")` | Raises `ValueError` | Manually verified (per README) |
| GC-06 | Reject an outage against a nonexistent substation | `Outage.report(conn, 9999, user_id, "desc")` | Currently no FK-existence check in `Outage.report`; relies on the GUI only offering substations from `Substation.all()` | Not yet executed — gap noted below |
| GC-07 | Assigning a work order moves its outage to "In Progress" | `WorkOrder.assign(conn, outage_id, tech_id, "2026-09-01")` | `Outage.status == "In Progress"` after assign | Manually verified (per README, part of the report→assign→complete→resolved sequence) |
| GC-08 | Reject a work order with no scheduled date | `WorkOrder.assign(conn, outage_id, tech_id, "")` | Raises `ValueError` | Not yet executed |
| GC-09 | Completing a work order resolves its outage | `WorkOrder.mark_complete(conn)` | Work order status "Completed"; linked outage status "Resolved" with `resolved_at` set | Manually verified (per README, part of the report→assign→complete→resolved sequence) |
| GC-10 | Duplicate outage records | Submit the same description against the same substation twice | Currently allowed (no uniqueness constraint); decide whether this should warn or be blocked | Not yet executed — gap noted below |
| GC-11 | Reject a complaint linked to a nonexistent outage | `Complaint.log(conn, user_id, "name", "desc", outage_id=9999)` | Raises `ValueError` | Manually verified (per README) |
| GC-12 | Reject a complaint with no customer name / description | `Complaint.log(conn, user_id, "", "desc")` | Raises `ValueError` | Not yet executed |
| GC-13 | Database/connection failure is handled gracefully | Simulate a locked/unreachable `gridcare.db` | App shows an error dialog rather than crashing | Not yet implemented — all DB calls are currently unguarded |
| GC-14 | Report accuracy: dashboard reflects current DB state | Insert an outage directly in SQLite, click "Refresh" | New row appears without restarting the app | Not yet executed |
| GC-15 | Password hashing | Inspect `users.password_hash` after `User.create(...)` | Value is a bcrypt hash, never the plaintext password | Not yet executed (implemented via `bcrypt.hashpw`, but no test confirms it against a live DB) |

## Known gaps to close before Week 4 formal testing

- **GC-06 / GC-10:** `Outage.report` and outage creation generally trust the
  caller for substation existence and don't reject duplicates. The GUI path
  is safe today (it only offers real substations via a combobox), but the
  model layer itself doesn't enforce it — add a check if `Outage.report` is
  ever called from anywhere else (e.g. a future API or bulk-import script).
- **GC-13:** no `try/except` around `sqlite3` calls anywhere in `models.py`
  or `app.py` yet. Add graceful handling before the Week 4 "database
  failures" test requirement.
- **GC-03:** role checks currently live only in which buttons `app.py`
  builds. The spec explicitly requires role separation to be enforced by
  "application logic and database permissions" too — worth adding a
  role check inside the model methods that matter most (`WorkOrder.assign`,
  `Outage.mark_resolved`) so a modified/malicious client can't bypass the
  GUI.

## Automated coverage still to write

No `tests/` directory exists yet for `gridcare-lite` (unlike
`grid-analysis`, which has full pytest coverage — see
`docs/coding_standards.md` for the pairing convention to follow). Plan: one
`tests/test_models.py` per class in `models.py`, run against a temporary
SQLite file (see `grid-analysis/tests/conftest.py` for the fixture pattern),
covering every row in the table above.
