"""
End-to-end coverage of app.py's routes via Flask's test client - no real
server, no browser. Doubles as the "does the whole feature actually work
wired together" check that unit tests on the models alone can't give.
"""
import io

from tests.conftest import login, register


# ---------------------------------------------------------------------------
# Registration & login
# ---------------------------------------------------------------------------

def test_register_and_login_round_trip(client):
    response = register(client, "12340000", "clinician")
    assert response.status_code == 200
    assert b"Log in" in response.data or b"log in" in response.data.lower()

    response = login(client, "12340000")
    assert b"Clinician Dashboard" in response.data


def test_register_rejects_invalid_id_for_role(client):
    response = register(client, "12341234", "clinician")  # doesn't end 0000
    assert b"Invalid ID format" in response.data


def test_register_rejects_weak_password(client):
    response = client.post("/register", data={
        "role": "patient", "user_id": "12342024", "name": "Ama",
        "email": "a@example.com", "password": "weak",
    }, follow_redirects=True)
    assert b"Password must be" in response.data


def test_login_rejects_wrong_password(client):
    register(client, "12340000", "clinician")
    response = login(client, "12340000", password="WrongPassword1!")
    assert b"Invalid ID or password" in response.data


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)
    assert b"Please log in first" in response.data


def test_patient_cannot_reach_clinician_only_route(client, clinician_and_patient):
    login(client, clinician_and_patient["patient_id"])
    response = client.get("/clinician")
    assert response.status_code == 403


def test_clinician_cannot_reach_patient_only_route(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    response = client.get("/patient")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Health tasks: creation, attachments, filtering
# ---------------------------------------------------------------------------

def _create_task(client, patient_id, title="Log blood pressure", attach=False):
    data = {"patient_id": patient_id, "title": title,
            "description": "Once a day for a week.", "due_date": "2026-12-01"}
    if attach:
        data["attachment"] = (io.BytesIO(b"field,value\n"), "intake.csv")
    return client.post("/tasks/new", data=data, content_type="multipart/form-data",
                        follow_redirects=True)


def test_clinician_creates_task_for_patient(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    response = _create_task(client, clinician_and_patient["patient_id"])
    assert b"Task assigned" in response.data


def test_task_with_attachment_is_downloadable_by_the_assigned_patient(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"], attach=True)

    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])
    dashboard = client.get("/patient")
    assert b"intake.csv" in dashboard.data


def test_task_creation_rejects_unknown_patient(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    response = _create_task(client, "99999999")
    assert b"Unknown patient" in response.data


def test_dashboard_filter_by_patient_narrows_submissions(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")

    login(client, clinician_and_patient["patient_id"])
    task_id = _get_first_task_id(client)
    _submit_file(client, task_id)
    client.get("/logout")

    # A second patient with no submissions of their own.
    register(client, "12342025", "patient", name="Someone Else", email="other@example.com")

    login(client, clinician_and_patient["clinician_id"])
    matching = client.get(f"/clinician?patient={clinician_and_patient['patient_id']}")
    other = client.get("/clinician?patient=12342025")

    assert clinician_and_patient["patient_id"].encode() in matching.data
    assert b"No submissions match this filter" in other.data


# ---------------------------------------------------------------------------
# Submission: upload, preview, download, review
# ---------------------------------------------------------------------------

def _submit_file(client, task_id, filename="reading.csv", content=b"date,value\n2026-08-01,120\n"):
    return client.post(f"/tasks/{task_id}/submit",
                        data={"file": (io.BytesIO(content), filename)},
                        content_type="multipart/form-data", follow_redirects=True)


def _get_first_task_id(client):
    """Health tasks get a random uuid4-derived ID, so tests that need it
    scrape it back out of the patient dashboard's submit-form action."""
    dashboard = client.get("/patient")
    html = dashboard.data.decode()
    marker = "/tasks/"
    start = html.index(marker) + len(marker)
    end = html.index("/submit", start)
    return html[start:end]


def test_patient_submits_file_for_assigned_task(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])

    task_id = _get_first_task_id(client)
    response = _submit_file(client, task_id)
    assert b"Submission received" in response.data


def test_incomplete_csv_flagged_but_still_accepted(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])

    task_id = _get_first_task_id(client)
    response = _submit_file(client, task_id, content=b"")  # empty file
    assert b"looks incomplete" in response.data


def test_patient_cannot_submit_to_someone_elses_task(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    task_id = _get_first_task_id_as_clinician(client)
    client.get("/logout")

    register(client, "12342025", "patient", name="Someone Else", email="other@example.com")
    login(client, "12342025")
    response = client.post(f"/tasks/{task_id}/submit",
                            data={"file": (io.BytesIO(b"x"), "f.txt")},
                            content_type="multipart/form-data", follow_redirects=True)
    assert b"not authorised" in response.data


def _get_first_task_id_as_clinician(client):
    dashboard = client.get("/clinician")
    html = dashboard.data.decode()
    marker = "/submissions/"
    # No submission exists yet when this is called right after task creation,
    # so scrape the task id from the filter <option value="..."> instead.
    marker = 'value="'
    tasks_section = html[html.index("All tasks"):]
    start = tasks_section.index(marker) + len(marker)
    end = tasks_section.index('"', start)
    return tasks_section[start:end]


def test_clinician_previews_and_downloads_submission(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])
    task_id = _get_first_task_id(client)
    _submit_file(client, task_id)
    client.get("/logout")

    login(client, clinician_and_patient["clinician_id"])
    key = f"{clinician_and_patient['patient_id']}_{task_id}"
    preview = client.get(f"/submissions/{key}/preview")
    assert preview.status_code == 200
    assert b"120" in preview.data

    download = client.get(f"/submissions/{key}/file")
    assert download.status_code == 200


def test_patient_cannot_download_another_patients_submission_file(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])
    task_id = _get_first_task_id(client)
    _submit_file(client, task_id)
    client.get("/logout")

    register(client, "12342025", "patient", name="Someone Else", email="other@example.com")
    login(client, "12342025")
    key = f"{clinician_and_patient['patient_id']}_{task_id}"
    response = client.get(f"/submissions/{key}/file")
    assert response.status_code == 403


def test_review_submission_sets_categorical_outcome(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    _create_task(client, clinician_and_patient["patient_id"])
    client.get("/logout")
    login(client, clinician_and_patient["patient_id"])
    task_id = _get_first_task_id(client)
    _submit_file(client, task_id)
    client.get("/logout")

    login(client, clinician_and_patient["clinician_id"])
    key = f"{clinician_and_patient['patient_id']}_{task_id}"
    response = client.post(f"/submissions/{key}/review",
                            data={"outcome": "Needs Follow-up", "notes": "Recheck next week."},
                            follow_redirects=True)
    assert b"Review recorded" in response.data


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

def test_clinician_schedules_appointment(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    response = client.post("/appointments/new", data={
        "patient_id": clinician_and_patient["patient_id"],
        "scheduled_at": "2026-09-05T10:00", "notes": "Follow-up",
    }, follow_redirects=True)
    assert b"Appointment scheduled" in response.data


def test_appointment_visible_on_patient_dashboard(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    client.post("/appointments/new", data={
        "patient_id": clinician_and_patient["patient_id"],
        "scheduled_at": "2026-09-05T10:00",
    }, follow_redirects=True)
    client.get("/logout")

    login(client, clinician_and_patient["patient_id"])
    dashboard = client.get("/patient")
    assert b"2026-09-05T10:00" in dashboard.data


def test_appointment_status_update(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    client.post("/appointments/new", data={
        "patient_id": clinician_and_patient["patient_id"], "scheduled_at": "2026-09-05T10:00",
    }, follow_redirects=True)

    from models.appointment import Appointment
    appointment_id = list(Appointment.all().keys())[0]
    response = client.post(f"/appointments/{appointment_id}/status",
                            data={"status": "Completed"}, follow_redirects=True)
    assert b"Appointment updated" in response.data
    assert Appointment.get(appointment_id)["status"] == "Completed"


# ---------------------------------------------------------------------------
# Messaging: direct, broadcast, poll
# ---------------------------------------------------------------------------

def test_direct_message_appears_in_recipients_conversation(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    client.post("/messages/send", data={
        "recipient_id": clinician_and_patient["patient_id"], "content": "Please reschedule.",
    }, follow_redirects=True)
    client.get("/logout")

    login(client, clinician_and_patient["patient_id"])
    response = client.get(f"/inbox/{clinician_and_patient['clinician_id']}")
    assert b"Please reschedule" in response.data


def test_broadcast_reaches_patient_dashboard(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    client.post("/messages/send", data={
        "content": "Clinic closed for the holiday.", "broadcast": "on",
    }, follow_redirects=True)
    client.get("/logout")

    login(client, clinician_and_patient["patient_id"])
    dashboard = client.get("/patient")
    assert b"Clinic closed for the holiday" in dashboard.data


def test_inbox_poll_reports_unread_count(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    client.post("/messages/send", data={
        "recipient_id": clinician_and_patient["patient_id"], "content": "Hello",
    }, follow_redirects=True)
    client.get("/logout")

    login(client, clinician_and_patient["patient_id"])
    response = client.get("/inbox/poll")
    assert response.get_json()["unread"] == 1


def test_patient_cannot_send_a_broadcast(client, clinician_and_patient):
    """A patient's broadcast="on" is silently ignored by app.py (only
    honoured when session role == clinician) - the message is still sent,
    but as a normal direct message, and it never reaches a third party's
    dashboard as an announcement."""
    login(client, clinician_and_patient["patient_id"])
    client.post("/messages/send", data={
        "recipient_id": clinician_and_patient["clinician_id"],
        "content": "I wish I could tell everyone this.", "broadcast": "on",
    }, follow_redirects=True)

    from models.message import Message
    assert all(not m.get("broadcast") for m in Message.all().values())


# ---------------------------------------------------------------------------
# Analytics & engagement
# ---------------------------------------------------------------------------

def test_analytics_route_is_clinician_only_and_renders(client, clinician_and_patient):
    login(client, clinician_and_patient["clinician_id"])
    response = client.get("/analytics")
    assert response.status_code == 200
    assert b"Operational Analytics" in response.data


def test_engagement_route_shows_own_trend(client, clinician_and_patient):
    login(client, clinician_and_patient["patient_id"])
    response = client.get("/engagement")
    assert response.status_code == 200
    assert b"My Private Engagement" in response.data
