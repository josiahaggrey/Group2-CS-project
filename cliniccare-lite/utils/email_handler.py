"""Email notification helper.

Falls back to console logging when SMTP credentials aren't configured, so the
app runs out of the box during development without real email credentials.
Set EMAIL_ADDRESS / EMAIL_PASSWORD environment variables (use a test/sandbox
account, never hard-code credentials) to send real emails.
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_email(recipient_email, subject, body):
    sender_email = os.environ.get("EMAIL_ADDRESS")
    sender_password = os.environ.get("EMAIL_PASSWORD")

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
