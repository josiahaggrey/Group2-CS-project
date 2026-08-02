# ClinicCare-Lite

A Flask + JSON clinic patient administration and communication system, with
role-based access for clinicians and patients.

**Scope boundary:** this system is strictly administrative and communication-only.
It must never diagnose patients, interpret symptoms, calculate risk, or recommend
treatment. The only "automated" feature is a structural form-completeness check
(`utils/validator.py`) — it flags missing columns/empty rows, never the meaning of
the data.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python app.py
```

Visit http://127.0.0.1:5000, register a clinician account (ID ending `0000`, e.g.
`12340000`) and a patient account (ID ending in a registration year 2022–2028, e.g.
`12342024`), then log in as each to try the workflow:

1. Clinician assigns a health task to a patient.
2. Patient uploads a `.txt`/`.csv`/`.pdf` submission.
3. Clinician reviews it with a categorical outcome (Pending / Reviewed — Normal /
   Needs Follow-up / Escalated) and notes.
4. Patient sees the outcome and their private Engagement Points.
5. Either side can send non-urgent messages via the Inbox; clinicians can also
   broadcast clinic-wide announcements.

Email notifications print to the console by default (see `utils/email_handler.py`).
Set `EMAIL_ADDRESS` / `EMAIL_PASSWORD` environment variables (a test/sandbox
account) to send real emails instead. Set `CLINICCARE_SECRET_KEY` before any real
deployment — the code ships with a dev-only fallback.

## What's implemented

- Registration/login with ID-format validation, password-complexity rules, and
  bcrypt hashing (`models/user.py`, `utils/validator.py`).
- Role-based dashboards and route protection (`app.py`).
- Health-task creation and assignment (`models/health_task.py`).
- Secure file submission: extension/size validation, systematic renaming
  (`patientID_taskID.ext`), per-patient storage directories
  (`models/task_submission.py`).
- Automated structural form-completeness check on `.csv`/`.txt` submissions.
- Categorical clinician review workflow with reviewer/date/outcome/notes.
- Private wellness-engagement tracker — patient-only visibility, never a
  leaderboard (`User.add_engagement_points`).
- In-app messaging + clinic-wide announcements with a persistent
  not-for-emergencies notice (`models/message.py`).
- JSON persistence with the `seek(0)` + `truncate()` fix applied everywhere
  (`utils/json_store.py`) — without it, overwriting a JSON file with a shorter
  payload leaves trailing bytes and corrupts the file on the next read.

## Known simplification / next steps

- **Single shared clinic**: all clinicians currently see all patients
  (`models/clinic.py: Clinic.get_or_create_default`). For multi-clinic scoping,
  extend registration to let a clinician create/select a clinic and change the
  clinician dashboard's patient query to `Clinic.patients_of(clinician_id)`.
- No file preview/download UI yet for clinicians (files are stored under
  `submissions/<patient_id>/`).
- No analytics dashboard yet (no-show rate, task-completion rate, review
  turnaround) — add a `/analytics` route using Plotly/Matplotlib per the course
  spec once enough demo data exists.
- No WebSocket/real-time messaging — inbox is currently poll-on-refresh.
- Add unit tests for `utils/validator.py`, the JSON save/load round-trip, and the
  file-upload validation path per the course testing requirements.
