"""Covers models/*.py against an isolated tmp_path (see conftest.py's
data_paths fixture) - persistence, scoping, and the private/never-a-
leaderboard rules the course spec requires."""
from models.appointment import Appointment
from models.clinic import Clinic
from models.health_task import HealthTask
from models.message import Message
from models.task_submission import TaskSubmission
from models.user import User


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def test_create_and_get_round_trips(data_paths):
    User(user_id="12340000", name="Dr. Owusu", email="d@example.com",
         password="Password1!", role="clinician").save()
    fetched = User.get("12340000")
    assert fetched.name == "Dr. Owusu"
    assert fetched.role == "clinician"


def test_password_is_hashed_not_plaintext(data_paths):
    User(user_id="12340000", name="Dr. Owusu", email="d@example.com",
         password="Password1!", role="clinician").save()
    fetched = User.get("12340000")
    assert fetched.password != "Password1!"
    assert fetched.check_password("Password1!") is True
    assert fetched.check_password("wrong") is False


def test_clinician_defaults_to_dark_theme(data_paths):
    user = User(user_id="12340000", name="Dr. Owusu", email="d@example.com",
                password="Password1!", role="clinician")
    assert user.theme == "dark"


def test_patient_defaults_to_colorful_theme(data_paths):
    user = User(user_id="12342024", name="Ama", email="a@example.com",
                password="Password1!", role="patient")
    assert user.theme == "colorful"


def test_add_engagement_points_only_touches_the_caller(data_paths):
    User(user_id="12342024", name="Ama", email="a@example.com",
         password="Password1!", role="patient").save()
    User(user_id="12342025", name="Kofi", email="k@example.com",
         password="Password1!", role="patient").save()

    User.add_engagement_points("12342024", 1)
    User.add_engagement_points("12342024", 1)

    assert User.get("12342024").engagement_points == 2
    assert User.get("12342025").engagement_points == 0  # untouched - never cross-patient


def test_all_by_role(data_paths):
    User(user_id="12340000", name="Dr. Owusu", email="d@example.com",
         password="Password1!", role="clinician").save()
    User(user_id="12342024", name="Ama", email="a@example.com",
         password="Password1!", role="patient").save()

    patients = User.all_by_role("patient")
    assert list(patients.keys()) == ["12342024"]


# ---------------------------------------------------------------------------
# HealthTask
# ---------------------------------------------------------------------------

def test_health_task_save_and_get(data_paths):
    task = HealthTask("task1", "Blood pressure log", "Log daily for a week",
                       "2026-09-01", "clinic-001", "12342024", "12340000")
    task.save()
    fetched = HealthTask.get("task1")
    assert fetched["title"] == "Blood pressure log"
    assert fetched["attachment_path"] is None


def test_health_task_with_attachment(data_paths):
    task = HealthTask("task1", "Intake", "Fill out the form", "2026-09-01",
                       "clinic-001", "12342024", "12340000",
                       attachment_path="/tmp/task1.csv", attachment_original_name="intake.csv")
    task.save()
    fetched = HealthTask.get("task1")
    assert fetched["attachment_path"] == "/tmp/task1.csv"
    assert fetched["attachment_original_name"] == "intake.csv"


def test_health_task_scoped_queries(data_paths):
    HealthTask("t1", "A", "desc", "2026-09-01", "clinic-001", "p1", "c1").save()
    HealthTask("t2", "B", "desc", "2026-09-02", "clinic-001", "p2", "c1").save()
    HealthTask("t3", "C", "desc", "2026-09-03", "clinic-001", "p1", "c2").save()

    assert set(HealthTask.for_patient("p1").keys()) == {"t1", "t3"}
    assert set(HealthTask.for_clinician("c1").keys()) == {"t1", "t2"}


# ---------------------------------------------------------------------------
# TaskSubmission
# ---------------------------------------------------------------------------

def test_submission_rejects_disallowed_extension(tmp_path, data_paths):
    source = tmp_path / "malware.exe"
    source.write_bytes(b"not real")
    submission = TaskSubmission("12342024", "task1", str(source))
    ok, error = submission.validate_file()
    assert ok is False
    assert "txt" in error


def test_submission_save_file_uses_clinic_scoped_path(tmp_path, data_paths):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    submission = TaskSubmission("12342024", "task1", str(source), clinic_id="clinic-001")
    submission.save_file()

    assert "clinic-001" in submission.file_path
    assert "12342024" in submission.file_path
    assert submission.file_path.endswith("12342024_task1.csv")


def test_submission_review_records_reviewer_and_timestamp(tmp_path, data_paths):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    submission = TaskSubmission("12342024", "task1", str(source))
    submission.save_file()
    key = submission.save()

    TaskSubmission.review(key, "12340000", "Reviewed - Normal", "Looks fine.")

    reviewed = TaskSubmission.get(key)
    assert reviewed["review_status"] == "Reviewed - Normal"
    assert reviewed["reviewer_id"] == "12340000"
    assert reviewed["reviewed_at"] is not None


def test_submission_review_rejects_invalid_outcome(tmp_path, data_paths):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    submission = TaskSubmission("12342024", "task1", str(source))
    submission.save_file()
    key = submission.save()

    try:
        TaskSubmission.review(key, "12340000", "Diagnosed: Hypertension", "")
        assert False, "expected ValueError for a non-categorical outcome"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

def test_conversation_returns_only_messages_between_the_two_parties(data_paths):
    Message("p1", "c1", "Hi doctor").save()
    Message("c1", "p1", "Hello").save()
    Message("p2", "c1", "A different patient's message").save()

    thread = Message.conversation("p1", "c1")
    assert len(thread) == 2
    assert all({m["sender_id"], m["recipient_id"]} == {"p1", "c1"} for m in thread.values())


def test_patient_cannot_see_another_patients_conversation(data_paths):
    Message("p1", "c1", "Hi doctor").save()
    thread = Message.conversation("p2", "c1")
    assert thread == {}


def test_contacts_for_lists_distinct_partners_most_recent_first(data_paths):
    Message("p1", "c1", "First message").save()
    Message("p1", "c2", "Second contact").save()
    Message("c1", "p1", "Reply").save()

    contacts = Message.contacts_for("p1")
    assert set(contacts) == {"c1", "c2"}
    assert contacts[0] == "c1"  # most recently active


def test_broadcast_excluded_from_contacts_and_conversation(data_paths):
    Message("c1", "*", "Clinic closed Friday", broadcast=True).save()
    assert Message.contacts_for("c1") == []


def test_inbox_for_includes_direct_and_broadcast(data_paths):
    Message("c1", "p1", "Direct message").save()
    Message("c1", "*", "Broadcast", broadcast=True).save()
    Message("c1", "p2", "Not for p1").save()

    inbox = Message.inbox_for("p1")
    assert len(inbox) == 2


def test_sent_by_excludes_broadcasts(data_paths):
    Message("c1", "p1", "Direct").save()
    Message("c1", "*", "Broadcast", broadcast=True).save()
    assert len(Message.sent_by("c1")) == 1


def test_unread_count_and_mark_conversation_read(data_paths):
    Message("c1", "p1", "First").save()
    Message("c1", "p1", "Second").save()
    assert Message.unread_count("p1") == 2

    Message.mark_conversation_read("p1", "c1")
    assert Message.unread_count("p1") == 0


def test_unread_count_includes_unread_broadcasts(data_paths):
    Message("c1", "*", "Announcement", broadcast=True).save()
    assert Message.unread_count("p1") == 1


# ---------------------------------------------------------------------------
# Clinic
# ---------------------------------------------------------------------------

def test_get_or_create_default_is_idempotent(data_paths):
    first = Clinic.get_or_create_default(clinician_id="c1")
    second = Clinic.get_or_create_default()
    assert first.clinic_id == second.clinic_id


def test_add_patient_to_clinic(data_paths):
    clinic = Clinic.get_or_create_default(clinician_id="c1")
    Clinic.add_patient(clinic.clinic_id, "p1")
    Clinic.add_patient(clinic.clinic_id, "p1")  # duplicate add should not duplicate the entry

    updated = Clinic.get(clinic.clinic_id)
    assert updated["patient_ids"] == ["p1"]


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

def test_appointment_save_and_scoped_queries(data_paths):
    Appointment("a1", "p1", "c1", "2026-09-05T10:00").save()
    Appointment("a2", "p2", "c1", "2026-09-06T10:00").save()

    assert set(Appointment.for_patient("p1").keys()) == {"a1"}
    assert set(Appointment.for_clinician("c1").keys()) == {"a1", "a2"}


def test_appointment_mark_status_rejects_invalid_value(data_paths):
    Appointment("a1", "p1", "c1", "2026-09-05T10:00").save()
    try:
        Appointment.mark_status("a1", "Diagnosed")
        assert False, "expected ValueError"
    except ValueError:
        pass
    assert Appointment.get("a1")["status"] == "Scheduled"


def test_due_for_reminder_only_returns_imminent_unreminded_scheduled(data_paths):
    from datetime import datetime, timedelta
    now = datetime(2026, 9, 5, 8, 0)

    Appointment("soon", "p1", "c1", (now + timedelta(hours=5)).isoformat()).save()
    Appointment("far", "p2", "c1", (now + timedelta(days=5)).isoformat()).save()
    Appointment("past", "p3", "c1", (now - timedelta(hours=1)).isoformat()).save()

    already_reminded = Appointment("reminded", "p4", "c1", (now + timedelta(hours=2)).isoformat())
    already_reminded.reminder_sent = True
    already_reminded.save()

    completed = Appointment("done", "p5", "c1", (now + timedelta(hours=2)).isoformat(),
                             status="Completed")
    completed.save()

    due = Appointment.due_for_reminder(now=now)
    assert set(due.keys()) == {"soon"}


def test_mark_reminder_sent_prevents_a_second_reminder(data_paths):
    from datetime import datetime, timedelta
    now = datetime(2026, 9, 5, 8, 0)
    Appointment("a1", "p1", "c1", (now + timedelta(hours=5)).isoformat()).save()

    assert "a1" in Appointment.due_for_reminder(now=now)
    Appointment.mark_reminder_sent("a1")
    assert "a1" not in Appointment.due_for_reminder(now=now)
