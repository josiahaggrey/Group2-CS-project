"""
Shared pytest fixtures for the cliniccare-lite test suite.

Puts the component's own directory on sys.path (flat modules, same as
gridcare-lite - `app.py`, `config.py`, `models/`, `utils/`). Every test
gets its own tmp_path, and `data_paths` redirects every model's JSON file
constant (and the submissions/attachments directories) there via
monkeypatch, so tests never touch the real data/ or submissions/ folders a
developer might have open.
"""
import os
import sys

import pytest

CLINICCARE_LITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CLINICCARE_LITE_DIR)


@pytest.fixture
def data_paths(tmp_path, monkeypatch):
    users_file = str(tmp_path / "users.json")
    health_tasks_file = str(tmp_path / "health_tasks.json")
    task_submissions_file = str(tmp_path / "task_submissions.json")
    messages_file = str(tmp_path / "messages.json")
    clinics_file = str(tmp_path / "clinics.json")
    appointments_file = str(tmp_path / "appointments.json")
    submissions_dir = str(tmp_path / "submissions")
    attachments_dir = str(tmp_path / "task_attachments")

    monkeypatch.setattr("models.user.USERS_FILE", users_file)
    monkeypatch.setattr("models.health_task.HEALTH_TASKS_FILE", health_tasks_file)
    monkeypatch.setattr("models.task_submission.TASK_SUBMISSIONS_FILE", task_submissions_file)
    monkeypatch.setattr("models.task_submission.SUBMISSIONS_DIR", submissions_dir)
    monkeypatch.setattr("models.message.MESSAGES_FILE", messages_file)
    monkeypatch.setattr("models.clinic.CLINICS_FILE", clinics_file)
    monkeypatch.setattr("models.appointment.APPOINTMENTS_FILE", appointments_file)
    monkeypatch.setattr("utils.file_handler.TASK_ATTACHMENTS_DIR", attachments_dir)

    return {
        "users": users_file, "health_tasks": health_tasks_file,
        "task_submissions": task_submissions_file, "messages": messages_file,
        "clinics": clinics_file, "appointments": appointments_file,
        "submissions_dir": submissions_dir, "attachments_dir": attachments_dir,
    }


@pytest.fixture
def client(data_paths):
    """A Flask test client wired to the isolated tmp_path data files."""
    import app as app_module
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def register(client, user_id, role, name="Test User", email="test@example.com",
             password="Password1!"):
    return client.post("/register", data={
        "role": role, "user_id": user_id, "name": name, "email": email, "password": password,
    }, follow_redirects=True)


def login(client, user_id, password="Password1!"):
    return client.post("/login", data={"user_id": user_id, "password": password},
                        follow_redirects=True)


@pytest.fixture
def clinician_and_patient(client):
    """Registers one clinician (12340000) and one patient (12342024),
    logged out afterward - tests log in as whichever role they need."""
    register(client, "12340000", "clinician", name="Dr. Owusu", email="clinician@example.com")
    register(client, "12342024", "patient", name="Ama Mensah", email="patient@example.com")
    client.get("/logout")
    return {"clinician_id": "12340000", "patient_id": "12342024"}
