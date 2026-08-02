"""
ClinicCare-Lite: a Flask + JSON clinic administration and communication system.

Scope boundary: this application is strictly administrative and communication-only.
It must never diagnose patients, interpret symptoms, or recommend treatment -
see check_form_completeness() in utils/validator.py for the only "automated"
feature, which is limited to structural validation of submitted files.
"""
import os
import tempfile
import uuid
from datetime import datetime, date
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                    session, url_for)

from config import REVIEW_OUTCOMES, SECRET_KEY
from models.clinic import Clinic
from models.health_task import HealthTask
from models.message import Message
from models.task_submission import TaskSubmission
from models.user import User
from utils.email_handler import send_email
from utils.validator import check_form_completeness

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    user_id = session.get("user_id")
    return User.get(user_id) if user_id else None


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role")
        user_id = request.form.get("user_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if role not in ("clinician", "patient"):
            flash("Invalid role.", "error")
            return render_template("register.html")
        if not User.validate_id(user_id, role):
            flash("Invalid ID format for the selected role.", "error")
            return render_template("register.html")
        if User.exists(user_id):
            flash("That ID is already registered.", "error")
            return render_template("register.html")
        if not name or not email:
            flash("Name and email are required.", "error")
            return render_template("register.html")
        if not User.validate_password(password):
            flash("Password must be 8+ characters with upper, lower, digit, and "
                  "special character.", "error")
            return render_template("register.html")

        user = User(user_id, name, email, password, role)
        user.save()

        clinic = Clinic.get_or_create_default(clinician_id=user_id if role == "clinician" else None)
        if role == "patient":
            Clinic.add_patient(clinic.clinic_id, user_id)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "")
        user = User.get(user_id)
        if user is None or not user.check_password(password):
            flash("Invalid ID or password.", "error")
            return render_template("login.html")

        session["user_id"] = user.user_id
        session["role"] = user.role
        session["username"] = user.name
        session["theme"] = user.theme
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/theme", methods=["POST"])
@login_required
def set_theme():
    theme = request.form.get("theme")
    if theme in ("colorful", "dark"):
        User.set_theme(session["user_id"], theme)
        session["theme"] = theme
    return redirect(request.referrer or url_for("dashboard"))


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    if session["role"] == "clinician":
        return redirect(url_for("clinician_dashboard"))
    return redirect(url_for("patient_dashboard"))


@app.route("/clinician")
@login_required
@role_required("clinician")
def clinician_dashboard():
    clinician_id = session["user_id"]
    patients = User.all_by_role("patient")
    tasks = HealthTask.for_clinician(clinician_id)
    submissions = TaskSubmission.all()

    pending = {k: v for k, v in submissions.items() if v["review_status"] == "Pending"}

    return render_template(
        "clinician_dashboard.html",
        patients=patients, tasks=tasks, submissions=submissions,
        pending_count=len(pending), review_outcomes=REVIEW_OUTCOMES,
    )


@app.route("/patient")
@login_required
@role_required("patient")
def patient_dashboard():
    patient_id = session["user_id"]
    tasks = HealthTask.for_patient(patient_id)
    submissions = TaskSubmission.for_patient(patient_id)
    user = current_user()

    return render_template(
        "patient_dashboard.html",
        tasks=tasks, submissions=submissions, engagement_points=user.engagement_points,
    )


# ---------------------------------------------------------------------------
# Health tasks
# ---------------------------------------------------------------------------
@app.route("/tasks/new", methods=["POST"])
@login_required
@role_required("clinician")
def create_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    patient_id = request.form.get("patient_id", "").strip()

    if not (title and description and due_date and patient_id):
        flash("All task fields are required.", "error")
        return redirect(url_for("clinician_dashboard"))
    if not User.exists(patient_id) or User.get(patient_id).role != "patient":
        flash("Unknown patient.", "error")
        return redirect(url_for("clinician_dashboard"))

    task_id = str(uuid.uuid4())[:8]
    clinic = Clinic.get_or_create_default(clinician_id=session["user_id"])
    task = HealthTask(task_id, title, description, due_date, clinic.clinic_id,
                       patient_id, session["user_id"])
    task.save()

    patient = User.get(patient_id)
    send_email(patient.email, "New health task assigned",
               f"You have a new task: {title} (due {due_date}).")

    flash("Task assigned.", "success")
    return redirect(url_for("clinician_dashboard"))


@app.route("/tasks/<task_id>/submit", methods=["POST"])
@login_required
@role_required("patient")
def submit_task(task_id):
    patient_id = session["user_id"]
    task = HealthTask.get(task_id)
    if task is None or task["assigned_patient_id"] != patient_id:
        flash("You are not authorised to submit to this task.", "error")
        return redirect(url_for("patient_dashboard"))

    uploaded = request.files.get("file")
    if not uploaded or uploaded.filename == "":
        flash("Please choose a file to submit.", "error")
        return redirect(url_for("patient_dashboard"))

    # Save to a temp path first; TaskSubmission.save_file() copies it into the
    # patient's own submissions directory under a systematic, timestamped name.
    tmp_path = os.path.join(tempfile.gettempdir(), f"upload_{uuid.uuid4().hex}_{uploaded.filename}")
    uploaded.save(tmp_path)

    try:
        submission = TaskSubmission(patient_id, task_id, tmp_path)
        submission.save_file()
        submission.save()
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("patient_dashboard"))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    issues = check_form_completeness(submission.file_path)
    if issues:
        flash("Submission saved, but the file looks incomplete: " + "; ".join(issues), "warning")
    else:
        flash("Submission received.", "success")

    if task.get("due_date"):
        try:
            on_time = date.today() <= datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            if on_time:
                User.add_engagement_points(patient_id, 1)
        except ValueError:
            pass  # malformed due_date - skip the engagement-point award, not the submission

    clinician = User.get(task["created_by"])
    if clinician:
        send_email(clinician.email, "New submission received",
                    f"Patient {patient_id} submitted for task '{task['title']}'.")

    return redirect(url_for("patient_dashboard"))


@app.route("/submissions/<key>/review", methods=["POST"])
@login_required
@role_required("clinician")
def review_submission(key):
    outcome = request.form.get("outcome")
    notes = request.form.get("notes", "").strip()
    submission = TaskSubmission.get(key)
    if submission is None:
        flash("Submission not found.", "error")
        return redirect(url_for("clinician_dashboard"))

    try:
        TaskSubmission.review(key, session["user_id"], outcome, notes)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("clinician_dashboard"))

    patient = User.get(submission["patient_id"])
    if patient:
        send_email(patient.email, "Your submission has been reviewed",
                    f"Outcome: {outcome}\nNotes: {notes or '(none)'}")

    flash("Review recorded.", "success")
    return redirect(url_for("clinician_dashboard"))


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------
@app.route("/inbox")
@login_required
def inbox():
    user_id = session["user_id"]
    messages = Message.inbox_for(user_id)
    return render_template("inbox.html", messages=messages)


@app.route("/messages/send", methods=["POST"])
@login_required
def send_message():
    recipient_id = request.form.get("recipient_id", "").strip()
    content = request.form.get("content", "").strip()
    broadcast = request.form.get("broadcast") == "on" and session["role"] == "clinician"

    if not content or (not broadcast and not User.exists(recipient_id)):
        flash("Message content and a valid recipient are required.", "error")
        return redirect(url_for("inbox"))

    message = Message(session["user_id"], recipient_id if not broadcast else "*", content, broadcast)
    message.save()
    flash("Message sent.", "success")
    return redirect(url_for("inbox"))


# ---------------------------------------------------------------------------
# Private engagement tracker (patient-only visibility - never a leaderboard)
# ---------------------------------------------------------------------------
@app.route("/engagement")
@login_required
@role_required("patient")
def engagement():
    user = current_user()
    return render_template("engagement.html", engagement_points=user.engagement_points)


if __name__ == "__main__":
    app.run(debug=True)
