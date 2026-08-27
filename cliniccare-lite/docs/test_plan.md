# Initial Test Plan — ClinicCare-Lite

Planning artifact for Week 1, per the course spec's Section 7 test
documentation format (objective / input / expected outcome / actual outcome
/ pass-fail / defect / corrective action / retest). Nothing below has an
automated or confirmed-manual test yet — `cliniccare-lite/README.md`'s
"Known simplification / next steps" section explicitly lists validator,
JSON round-trip, and file-upload tests as still to add. This table is the
coverage plan those tests should satisfy, execution tracked as each lands.

| ID | Objective | Input | Expected outcome | Status |
|---|---|---|---|---|
| CC-01 | Reject an invalid clinician ID | Register with an 8-digit ID not ending in `0000` as role `clinician` | `User.validate_id` returns `False`; registration rejected | Not yet executed |
| CC-02 | Reject an invalid patient ID | Register with an ID ending in a year outside 2022-2028 as role `patient` | `User.validate_id` returns `False`; registration rejected | Not yet executed |
| CC-03 | Reject a weak password | Register with a password missing a digit or special character | `User.validate_password` returns `False`; registration rejected | Not yet executed |
| CC-04 | Reject an incorrect login | Correct ID, wrong password | `check_password` returns `False`; login rejected | Not yet executed |
| CC-05 | Unauthorised record access: patient cannot view another patient's tasks | Log in as patient A, attempt to reach patient B's task list | `/patient` derives `patient_id` from `session["user_id"]` only (`app.py:177`), never from a URL/form param, so there's no ID to substitute — but no explicit test confirms this | Not yet executed (design already appears sound on inspection) |
| CC-06 | Unauthorised record access: patient cannot view another patient's messages | Log in as patient A, attempt to reach patient B's inbox | `/inbox` likewise derives `user_id` from `session` (`app.py:306`) | Not yet executed (design already appears sound on inspection) |
| CC-07 | Reject an unsupported file type | Submit a `.exe` or `.docx` file for a health task | `validate_file` returns `False`; upload rejected before reaching disk | Not yet executed |
| CC-08 | Reject an oversized file | Submit a file larger than `MAX_FILE_SIZE_BYTES` (5 MB) | `validate_file` returns `False`; upload rejected | Not yet executed |
| CC-09 | Missing required fields on task creation | Create a health task with no title or due date | Route/form validation rejects with a clear message | Not yet executed |
| CC-10 | Incorrect task ownership | Patient submits a file against a `task_id` not assigned to them | `/tasks/<task_id>/submit` explicitly checks `task["assigned_patient_id"] != patient_id` and rejects otherwise (`app.py:227`) | Not yet executed (check already implemented) |
| CC-11 | Duplicate submissions | Patient submits twice for the same `task_id` | `TaskSubmission.save()` uses `f"{patient_id}_{task_id}"` as the key, so a second submission currently **overwrites** the first | Not yet executed — behaviour needs a product decision, see Known Gaps |
| CC-12 | Messaging privacy | Patient A requests `Message.conversation(patient_B, clinician)` | Should not return messages A isn't part of | Not yet executed |
| CC-13 | Broadcast announcements reach every patient's inbox | Clinician sends a `broadcast=True` message | `Message.inbox_for(any_patient_id)` includes it | Not yet executed |
| CC-14 | Notification failure is handled gracefully | SMTP send fails (bad credentials / no network) | App logs/prints the failure and continues, doesn't crash the request | Not yet executed — confirm `utils/email_handler.py`'s console-fallback behaviour under a forced failure, not just missing credentials |
| CC-15 | Patient-data exposure in analytics | (Analytics dashboard not yet implemented — see README) | When built: clinician view is aggregate-only, patient view is own-data-only | Blocked on feature; test plan placeholder |
| CC-16 | Diagnostic-scope violation | Inspect every route/model for symptom interpretation, risk scoring, or treatment suggestion | None found — `TaskSubmission`'s automated check is structural only (missing/empty fields), never interprets values | Reviewed at design time (this session) — recommend a standing checklist item in code review, not a one-time check |
| CC-17 | Form-completeness check flags a missing column | Submit a `.csv` missing an expected column | Validator reports which field is missing, doesn't interpret the data | Not yet executed |
| CC-18 | Engagement Points never exposed cross-patient | Attempt to fetch another patient's `engagement_points` via any route | No route/model method takes an arbitrary patient ID from an unauthenticated or cross-account caller | Not yet executed |

## Known gaps to close before Week 4 formal testing

- **CC-05 / CC-06 / CC-10:** authorization for these is enforced in
  `app.py`'s route handlers (session-scoped IDs, explicit ownership checks)
  rather than in the model layer itself — confirmed correct for the routes
  reviewed here (`/patient`, `/inbox`, `/tasks/<task_id>/submit`), but this
  pattern needs re-checking by hand on every *new* route that takes a
  `patient_id`/`task_id` from a URL or form param, since nothing enforces it
  structurally (e.g. a decorator).
- **CC-11:** `TaskSubmission.save()` silently overwrites a prior submission
  for the same task because the JSON key is `patient_id_task_id` with no
  uniqueness check. Decide the intended behaviour (block resubmission,
  version it, or allow overwrite as "the current answer") and encode it
  explicitly rather than leaving it as incidental key-collision behaviour.
- **CC-15:** the analytics dashboard doesn't exist yet (see
  `cliniccare-lite/README.md`), so this test is blocked until that feature
  lands — kept here so the privacy requirement isn't forgotten when it's
  built.

## Automated coverage still to write

Mirrors the gap the component README already flags: unit tests for
`utils/validator.py` (ID/password rules, CC-01 through CC-03), the JSON
save/load round-trip including the `truncate()` fix in `json_store.py`, and
the file-upload validation path (CC-07, CC-08). Follow the pairing
convention in `docs/coding_standards.md` — e.g.
`tests/test_validator.py` next to `utils/validator.py`.
