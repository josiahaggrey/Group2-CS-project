"""Email notification helper.

Matches the course spec's sample signature exactly - send_email() takes the
sender's credentials as parameters rather than reading them internally, so
the caller (app.py, send_appointment_reminders.py) owns sourcing them from
EMAIL_ADDRESS / EMAIL_PASSWORD environment variables (see config.py), never
hard-coded. Falls back to console logging when they're empty, so the app
runs out of the box during development without real email credentials.
"""
import smtplib
from email.mime.text import MIMEText


def send_email(sender_email, sender_password, recipient_email, subject, body):
    if not sender_email or not sender_password:
        print(f"[email stub] To: {recipient_email} | Subject: {subject}\n{body}\n")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
