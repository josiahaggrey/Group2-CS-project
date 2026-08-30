import os
import shutil
from datetime import datetime

from config import MAX_FILE_SIZE_BYTES, REVIEW_OUTCOMES, SUBMISSIONS_DIR, TASK_SUBMISSIONS_FILE
from utils.file_handler import is_allowed_extension
from utils.json_store import load_json, save_json


class TaskSubmission:
    def __init__(self, patient_id, task_id, source_file_path, clinic_id="clinic-001"):
        self.patient_id = patient_id
        self.task_id = task_id
        self.source_file_path = source_file_path
        self.clinic_id = clinic_id
        self.file_path = None
        self.timestamp = datetime.now().isoformat()
        self.review_status = "Pending"
        self.notes = None
        self.reviewer_id = None
        self.reviewed_at = None

    def validate_file(self):
        if not is_allowed_extension(self.source_file_path):
            return False, "Only .txt, .csv, and .pdf files are allowed."
        if os.path.getsize(self.source_file_path) > MAX_FILE_SIZE_BYTES:
            return False, "File exceeds the maximum allowed size (5 MB)."
        return True, None

    def save_file(self):
        ok, error = self.validate_file()
        if not ok:
            raise ValueError(error)
        # clinic_id, patient_id, and task_id are all validated upstream (a
        # known clinic, an 8-digit patient ID, an existing task key), so
        # they're safe to use directly in a filesystem path.
        ext = os.path.splitext(self.source_file_path)[1].lower()
        dest_dir = os.path.join(SUBMISSIONS_DIR, str(self.clinic_id), str(self.patient_id))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{self.patient_id}_{self.task_id}{ext}")
        shutil.copy(self.source_file_path, dest_path)
        self.file_path = dest_path

    def save(self):
        data = load_json(TASK_SUBMISSIONS_FILE)
        key = f"{self.patient_id}_{self.task_id}"
        data[key] = {
            "patient_id": self.patient_id,
            "task_id": self.task_id,
            "clinic_id": self.clinic_id,
            "file_path": self.file_path,
            "timestamp": self.timestamp,
            "review_status": self.review_status,
            "notes": self.notes,
            "reviewer_id": self.reviewer_id,
            "reviewed_at": self.reviewed_at,
        }
        save_json(TASK_SUBMISSIONS_FILE, data)
        return key

    @staticmethod
    def all():
        return load_json(TASK_SUBMISSIONS_FILE)

    @staticmethod
    def for_patient(patient_id):
        return {k: v for k, v in load_json(TASK_SUBMISSIONS_FILE).items()
                if v["patient_id"] == patient_id}

    @staticmethod
    def get(key):
        return load_json(TASK_SUBMISSIONS_FILE).get(key)

    @staticmethod
    def review(key, reviewer_id, outcome, notes):
        if outcome not in REVIEW_OUTCOMES:
            raise ValueError(f"Invalid review outcome: {outcome}")
        data = load_json(TASK_SUBMISSIONS_FILE)
        if key not in data:
            raise KeyError("Submission not found.")
        data[key]["review_status"] = outcome
        data[key]["notes"] = notes
        data[key]["reviewer_id"] = reviewer_id
        data[key]["reviewed_at"] = datetime.now().isoformat()
        save_json(TASK_SUBMISSIONS_FILE, data)
