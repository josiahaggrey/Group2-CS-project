"""Central configuration for ClinicCare-Lite: paths and validation constants."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")

USERS_FILE = os.path.join(DATA_DIR, "users.json")
HEALTH_TASKS_FILE = os.path.join(DATA_DIR, "health_tasks.json")
TASK_SUBMISSIONS_FILE = os.path.join(DATA_DIR, "task_submissions.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")
CLINICS_FILE = os.path.join(DATA_DIR, "clinics.json")

ALLOWED_EXTENSIONS = {".txt", ".csv", ".pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

REVIEW_OUTCOMES = ("Pending", "Reviewed - Normal", "Needs Follow-up", "Escalated")

# Flask secret key: read from the environment in real deployments. A dev fallback
# is provided so the starter app runs out of the box; override with a real secret
# via the CLINICCARE_SECRET_KEY environment variable before any real deployment.
SECRET_KEY = os.environ.get("CLINICCARE_SECRET_KEY", "dev-only-change-me")
