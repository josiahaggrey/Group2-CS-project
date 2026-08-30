"""Send appointment reminder emails for appointments in the next 24 hours.

A Flask dev server has no built-in job scheduler, so the "scheduled job"
the course spec describes (send a reminder 24 hours before an appointment)
lives here as a standalone script rather than inside app.py. Run it on a
schedule via cron, Windows Task Scheduler, or similar:

    python send_appointment_reminders.py

Safe to run as often as you like - Appointment.due_for_reminder() only
returns appointments that are still "Scheduled" and haven't already had
reminder_sent set, so a second run in the same day sends nothing new.
"""
from config import EMAIL_ADDRESS, EMAIL_PASSWORD
from models.appointment import Appointment
from models.user import User
from utils.email_handler import send_email


def main():
    due = Appointment.due_for_reminder()
    for appointment_id, appointment in due.items():
        patient = User.get(appointment["patient_id"])
        if patient is None:
            continue
        send_email(
            EMAIL_ADDRESS, EMAIL_PASSWORD, patient.email, "Appointment reminder",
            f"Reminder: you have an appointment scheduled for "
            f"{appointment['scheduled_at']}."
            + (f" Notes: {appointment['notes']}" if appointment.get("notes") else ""),
        )
        Appointment.mark_reminder_sent(appointment_id)
    print(f"Sent {len(due)} appointment reminder(s).")


if __name__ == "__main__":
    main()
