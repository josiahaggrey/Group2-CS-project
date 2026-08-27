"""
Read-only operational analytics for ClinicCare-Lite - the clinician
Analytics screen and the patient's own trend view. Mirrors gridcare-lite's
Report class: every method only aggregates data the other models already
wrote, nothing here mutates anything.

Scope boundary applies here too: these are operational counts (how many,
how fast, how often), never anything that interprets a patient's health
data or compares one patient against another.
"""
from datetime import datetime

from config import REVIEW_OUTCOMES
from models.appointment import Appointment
from models.health_task import HealthTask
from models.task_submission import TaskSubmission


class Analytics:
    @staticmethod
    def task_completion_rate():
        """% of tasks with at least one submission - None if there are no
        tasks yet, so the template can show "no data" instead of 0%."""
        tasks = HealthTask.all()
        if not tasks:
            return None
        submitted_task_ids = {s["task_id"] for s in TaskSubmission.all().values()}
        completed = sum(1 for task_id in tasks if task_id in submitted_task_ids)
        return round(100 * completed / len(tasks), 1)

    @staticmethod
    def pending_review_count():
        return sum(1 for s in TaskSubmission.all().values() if s["review_status"] == "Pending")

    @staticmethod
    def average_review_turnaround_hours():
        hours = []
        for submission in TaskSubmission.all().values():
            if not submission.get("reviewed_at"):
                continue
            try:
                submitted_at = datetime.fromisoformat(submission["timestamp"])
                reviewed_at = datetime.fromisoformat(submission["reviewed_at"])
            except (ValueError, TypeError):
                continue
            hours.append((reviewed_at - submitted_at).total_seconds() / 3600)
        return round(sum(hours) / len(hours), 1) if hours else None

    @staticmethod
    def monthly_task_volume():
        """{'2026-08': 3, ...} - tasks don't record a created-at, so this
        buckets by due_date's year-month instead, sorted chronologically."""
        counts = {}
        for task in HealthTask.all().values():
            month = task.get("due_date", "")[:7]
            if month:
                counts[month] = counts.get(month, 0) + 1
        return dict(sorted(counts.items()))

    @staticmethod
    def submission_status_breakdown():
        counts = {outcome: 0 for outcome in REVIEW_OUTCOMES}
        for submission in TaskSubmission.all().values():
            status = submission["review_status"]
            counts[status] = counts.get(status, 0) + 1
        return counts

    @staticmethod
    def appointment_no_show_rate():
        """None until at least one appointment has actually happened (or
        been missed) - a rate over zero completed appointments is
        meaningless, not zero."""
        past = [a for a in Appointment.all().values() if a["status"] in ("Completed", "No-Show")]
        if not past:
            return None
        no_shows = sum(1 for a in past if a["status"] == "No-Show")
        return round(100 * no_shows / len(past), 1)

    @staticmethod
    def clinician_summary():
        """Everything the Analytics screen needs, in one call."""
        return {
            "task_completion_rate": Analytics.task_completion_rate(),
            "pending_review_count": Analytics.pending_review_count(),
            "average_review_turnaround_hours": Analytics.average_review_turnaround_hours(),
            "monthly_task_volume": Analytics.monthly_task_volume(),
            "submission_status_breakdown": Analytics.submission_status_breakdown(),
            "appointment_no_show_rate": Analytics.appointment_no_show_rate(),
        }

    @staticmethod
    def patient_trend(patient_id):
        """A patient's own history over time - never compared against
        another patient (same rule as the Engagement Points tracker)."""
        submissions = TaskSubmission.for_patient(patient_id)
        by_month = {}
        for submission in submissions.values():
            month = submission["timestamp"][:7]
            by_month[month] = by_month.get(month, 0) + 1

        appointments = Appointment.for_patient(patient_id)
        attended = sum(1 for a in appointments.values() if a["status"] == "Completed")
        missed = sum(1 for a in appointments.values() if a["status"] == "No-Show")

        return {
            "submissions_by_month": dict(sorted(by_month.items())),
            "total_submissions": len(submissions),
            "appointments_attended": attended,
            "appointments_missed": missed,
        }
