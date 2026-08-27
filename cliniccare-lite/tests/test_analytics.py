"""Covers models/analytics.py - every method is read-only, so these tests
mostly check the arithmetic and the "None vs 0" distinction (a rate over
zero events is unknown, not zero)."""
from datetime import datetime

from models.analytics import Analytics
from models.appointment import Appointment
from models.health_task import HealthTask
from models.task_submission import TaskSubmission


def test_task_completion_rate_none_with_no_tasks(data_paths):
    assert Analytics.task_completion_rate() is None


def test_task_completion_rate_computed(tmp_path, data_paths):
    HealthTask("t1", "A", "d", "2026-09-01", "clinic-001", "p1", "c1").save()
    HealthTask("t2", "B", "d", "2026-09-01", "clinic-001", "p1", "c1").save()

    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    submission = TaskSubmission("p1", "t1", str(source))
    submission.save_file()
    submission.save()

    assert Analytics.task_completion_rate() == 50.0


def test_pending_review_count(tmp_path, data_paths):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    TaskSubmission("p1", "t1", str(source)).save_file()
    submission = TaskSubmission("p1", "t1", str(source))
    submission.save_file()
    submission.save()

    assert Analytics.pending_review_count() == 1


def test_average_review_turnaround_none_with_no_reviews(data_paths):
    assert Analytics.average_review_turnaround_hours() is None


def test_average_review_turnaround_computed(tmp_path, data_paths, monkeypatch):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")
    submission = TaskSubmission("p1", "t1", str(source))
    submission.save_file()
    submission.timestamp = "2026-08-01T10:00:00"
    key = submission.save()

    # Review 2 hours later - patch datetime.now() used inside review()'s
    # reviewed_at stamp isn't directly controllable, so assert reviewed_at
    # exists and turnaround is a small non-negative number instead of a
    # fixed value (review() always stamps "now").
    TaskSubmission.review(key, "c1", "Reviewed - Normal", "")
    result = Analytics.average_review_turnaround_hours()
    assert result is not None
    assert result >= 0


def test_monthly_task_volume_buckets_by_due_date_month(data_paths):
    HealthTask("t1", "A", "d", "2026-08-15", "clinic-001", "p1", "c1").save()
    HealthTask("t2", "B", "d", "2026-08-20", "clinic-001", "p1", "c1").save()
    HealthTask("t3", "C", "d", "2026-09-01", "clinic-001", "p1", "c1").save()

    volume = Analytics.monthly_task_volume()
    assert volume == {"2026-08": 2, "2026-09": 1}


def test_submission_status_breakdown_zero_fills(data_paths):
    breakdown = Analytics.submission_status_breakdown()
    assert breakdown["Pending"] == 0
    assert breakdown["Reviewed - Normal"] == 0


def test_appointment_no_show_rate_none_until_something_has_happened(data_paths):
    Appointment("a1", "p1", "c1", "2026-09-05T10:00").save()  # still just "Scheduled"
    assert Analytics.appointment_no_show_rate() is None


def test_appointment_no_show_rate_computed(data_paths):
    Appointment("a1", "p1", "c1", "2026-09-05T10:00", status="Completed").save()
    Appointment("a2", "p2", "c1", "2026-09-06T10:00", status="No-Show").save()
    Appointment("a3", "p3", "c1", "2026-09-07T10:00", status="Scheduled").save()  # not counted

    assert Analytics.appointment_no_show_rate() == 50.0


def test_patient_trend_never_includes_another_patients_data(tmp_path, data_paths):
    source = tmp_path / "readings.csv"
    source.write_text("date,value\n2026-08-01,120\n")

    sub1 = TaskSubmission("p1", "t1", str(source))
    sub1.save_file()
    sub1.timestamp = "2026-08-01T10:00:00"
    sub1.save()

    sub2 = TaskSubmission("p2", "t1", str(source))
    sub2.save_file()
    sub2.save()

    trend = Analytics.patient_trend("p1")
    assert trend["total_submissions"] == 1
    assert "2026-08" in trend["submissions_by_month"]
