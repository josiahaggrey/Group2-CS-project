# ClinicCare-Lite

A Flask + JSON clinic patient administration and communication system, with
role-based access for clinicians and patients.

**Scope boundary:** this system is strictly administrative and communication-only.
It must never diagnose patients, interpret symptoms, calculate risk, or recommend
treatment. The only "automated" features are structural: the form-completeness
check (`utils/validator.py`) flags missing columns/empty rows, never the meaning
of the data, and the analytics screens (`models/analytics.py`) report operational
counts (how many, how fast), never anything clinical or patient-to-patient.

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

1. Clinician assigns a health task to a patient, optionally with a file attachment.
2. Patient uploads a `.txt`/`.csv`/`.pdf` submission; both patient and clinician
   get an email notification (console-logged by default).
3. Clinician previews (`.csv`/`.txt`) or downloads the file, then reviews it with
   a categorical outcome (Pending / Reviewed — Normal / Needs Follow-up /
   Escalated) and notes.
4. Patient sees the outcome, their private Engagement Points, and a submission
   trend at `/engagement`.
5. Clinician schedules an appointment for a patient; it shows up on the
   patient's dashboard and (run separately, see below) gets a 24-hour
   reminder email.
6. Either side can message the other via the Inbox's per-contact
   conversation threads; clinicians can also broadcast an announcement
   (optionally marked urgent, which emails every patient) that appears on
   every patient's dashboard.
7. Clinician reviews operational analytics at `/analytics`: task completion
   rate, pending reviews, average review turnaround, monthly task volume,
   submission-outcome breakdown, and appointment no-show rate.

Email notifications print to the console by default (see `utils/email_handler.py`).
Set `EMAIL_ADDRESS` / `EMAIL_PASSWORD` environment variables (a test/sandbox
account) to send real emails instead. Set `CLINICCARE_SECRET_KEY` before any real
deployment — the code ships with a dev-only fallback.

### Appointment reminders

Flask's dev server has no built-in job scheduler, so the "send a reminder
24 hours before" requirement is a standalone script rather than something
`app.py` runs itself:

```bash
python send_appointment_reminders.py
```

Run it on a schedule (cron, Windows Task Scheduler) in a real deployment.
Safe to run repeatedly — `Appointment.due_for_reminder()` only returns
appointments that haven't been reminded yet.

### Tests

```bash
pytest
```

97 tests: `utils/validator.py`, `utils/json_store.py` (including a
regression test for the `truncate()` fix), `utils/file_handler.py`, every
model, and full Flask-test-client coverage of every route in `app.py`
(including authorization checks — a patient can't reach a clinician-only
route or another patient's files).

## What's implemented

- Registration/login with ID-format validation, password-complexity rules, and
  bcrypt hashing (`models/user.py`, `utils/validator.py`), backed by **live
  client-side validation** (`static/scripts.js`) that mirrors the same rules
  for immediate feedback before the server round-trip.
- Role-based dashboards and route protection (`app.py`).
- Health-task creation and assignment, with an **optional file attachment**
  the assigned patient can download (`models/health_task.py`).
- **Filterable submission dashboard** (by patient and/or task) for clinicians.
- Secure file submission: extension/size validation, systematic renaming
  (`patientID_taskID.ext`), **clinic-scoped** storage directories
  (`submissions/<clinicID>/<patientID>/`, `models/task_submission.py`).
- **Clinician file preview** (table view for `.csv`, raw text for `.txt`) and
  **download**, for every file type including `.pdf`.
- Automated structural form-completeness check on `.csv`/`.txt` submissions.
- Categorical clinician review workflow with reviewer/date/outcome/notes.
- **Appointment scheduling** (`models/appointment.py`): clinicians book a
  slot for a patient, update its status (Scheduled/Completed/No-Show/
  Cancelled), and `send_appointment_reminders.py` emails a reminder 24
  hours out.
- Private wellness-engagement tracker — patient-only visibility, never a
  leaderboard (`User.add_engagement_points`) — now paired with a **personal
  submission trend** at `/engagement` (own data only, per `models/analytics.py`).
- **Operational analytics dashboard** for clinicians (`/analytics`): task
  completion rate, pending reviews, average review turnaround, monthly task
  volume, submission-outcome breakdown, appointment no-show rate.
- **Threaded, per-contact messaging** in a single two-pane `templates/chat.html`
  (conversation list + announcements + sent on the left, the active thread on
  the right) — matching the course spec's own suggested directory structure,
  which names this file `chat.html`, not a separate inbox/conversation split.
  `models/message.py: contacts_for()` / `sent_by()` back the sidebar; the
  search boxes filter both the conversation list and announcements client-side.
- **Clinic-wide announcements now appear on the patient dashboard**, not just
  the inbox, with an optional "urgent" flag that emails every patient.
- **Near-real-time unread badge**: the inbox unread count polls `/inbox/poll`
  every 15 seconds via `fetch()` — periodic polling, the course spec's
  explicitly-allowed alternative to a full WebSocket server.
- **Responsive layout** (`static/styles.css`): a collapsing mobile nav,
  horizontally-scrollable tables instead of a broken layout on narrow
  screens, and no hard-coded fixed widths — a lightweight hand-written
  alternative to pulling in Bootstrap from a CDN.
- JSON persistence with the `seek(0)` + `truncate()` fix applied everywhere
  (`utils/json_store.py`) — without it, overwriting a JSON file with a shorter
  payload leaves trailing bytes and corrupts the file on the next read.

## Known simplification / next steps

- **Single shared clinic**: all clinicians currently see all patients
  (`models/clinic.py: Clinic.get_or_create_default`). For multi-clinic scoping,
  extend registration to let a clinician create/select a clinic and change the
  clinician dashboard's patient query to `Clinic.patients_of(clinician_id)`.
  (Submission storage is already clinic-scoped on disk, ready for this.)
- **Polling, not WebSockets**, for near-real-time messaging — a deliberate
  scope choice (see "What's implemented" above) since Flask-SocketIO needs
  an async worker (eventlet/gevent) this prototype doesn't otherwise need.
  Revisit if the team wants true push updates.
- **Appointment reminders are a standalone script**, not a background job
  inside `app.py` — see "Appointment reminders" above.
- A registered clinician can currently message any user ID via the Inbox's
  "Send a Message" form, not strictly scoped to "their" patients — harmless
  today (one shared clinic), worth tightening alongside multi-clinic support.
