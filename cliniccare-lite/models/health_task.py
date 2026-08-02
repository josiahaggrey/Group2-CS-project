from config import HEALTH_TASKS_FILE
from utils.json_store import load_json, save_json


class HealthTask:
    def __init__(self, task_id, title, description, due_date, clinic_id,
                 assigned_patient_id, created_by):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.clinic_id = clinic_id
        self.assigned_patient_id = assigned_patient_id
        self.created_by = created_by

    def save(self):
        data = load_json(HEALTH_TASKS_FILE)
        data[self.task_id] = {
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "clinic_id": self.clinic_id,
            "assigned_patient_id": self.assigned_patient_id,
            "created_by": self.created_by,
        }
        save_json(HEALTH_TASKS_FILE, data)

    @staticmethod
    def all():
        return load_json(HEALTH_TASKS_FILE)

    @staticmethod
    def get(task_id):
        return load_json(HEALTH_TASKS_FILE).get(task_id)

    @staticmethod
    def for_patient(patient_id):
        return {tid: t for tid, t in load_json(HEALTH_TASKS_FILE).items()
                if t.get("assigned_patient_id") == patient_id}

    @staticmethod
    def for_clinician(clinician_id):
        return {tid: t for tid, t in load_json(HEALTH_TASKS_FILE).items()
                if t.get("created_by") == clinician_id}
