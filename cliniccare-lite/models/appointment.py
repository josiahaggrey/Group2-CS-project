"""
Appointment scheduling for ClinicCare-Lite.

Strictly administrative, like every other model here: who, when, and
whether it happened - never why, and never anything clinical. A clinician
schedules one against a patient; `due_for_reminder()` is what a scheduled
job (see scripts/send_appointment_reminders.py) polls to find appointments
needing a 24-hour reminder email.
"""
from datetime import datetime

from config import APPOINTMENTS_FILE
from utils.json_store import load_json, save_json

VALID_STATUSES = ("Scheduled", "Completed", "No-Show", "Cancelled")


class Appointment:
    def __init__(self, appointment_id, patient_id, clinician_id, scheduled_at,
                 notes="", status="Scheduled", reminder_sent=False):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.clinician_id = clinician_id
        self.scheduled_at = scheduled_at  # ISO 8601, e.g. "2026-09-05T10:00"
        self.notes = notes
        self.status = status
        self.reminder_sent = reminder_sent

    def save(self):
        data = load_json(APPOINTMENTS_FILE)
        data[self.appointment_id] = {
            "patient_id": self.patient_id,
            "clinician_id": self.clinician_id,
            "scheduled_at": self.scheduled_at,
            "notes": self.notes,
            "status": self.status,
            "reminder_sent": self.reminder_sent,
        }
        save_json(APPOINTMENTS_FILE, data)

    @staticmethod
    def all():
        return load_json(APPOINTMENTS_FILE)

    @staticmethod
    def get(appointment_id):
        return load_json(APPOINTMENTS_FILE).get(appointment_id)

    @staticmethod
    def for_patient(patient_id):
        return {aid: a for aid, a in load_json(APPOINTMENTS_FILE).items()
                if a["patient_id"] == patient_id}

    @staticmethod
    def for_clinician(clinician_id):
        return {aid: a for aid, a in load_json(APPOINTMENTS_FILE).items()
                if a["clinician_id"] == clinician_id}

    @staticmethod
    def due_for_reminder(now=None):
        """Appointments still 'Scheduled', not yet reminded, within the
        next 24 hours of `now` - what the reminder script queries."""
        now = now or datetime.now()
        due = {}
        for appointment_id, appointment in load_json(APPOINTMENTS_FILE).items():
            if appointment["status"] != "Scheduled" or appointment.get("reminder_sent"):
                continue
            try:
                scheduled_at = datetime.fromisoformat(appointment["scheduled_at"])
            except ValueError:
                continue
            hours_until = (scheduled_at - now).total_seconds() / 3600
            if 0 <= hours_until <= 24:
                due[appointment_id] = appointment
        return due

    @staticmethod
    def mark_reminder_sent(appointment_id):
        data = load_json(APPOINTMENTS_FILE)
        if appointment_id in data:
            data[appointment_id]["reminder_sent"] = True
            save_json(APPOINTMENTS_FILE, data)

    @staticmethod
    def mark_status(appointment_id, status):
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}.")
        data = load_json(APPOINTMENTS_FILE)
        if appointment_id in data:
            data[appointment_id]["status"] = status
            save_json(APPOINTMENTS_FILE, data)
