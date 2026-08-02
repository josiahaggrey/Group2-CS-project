from config import CLINICS_FILE
from utils.json_store import load_json, save_json

DEFAULT_CLINIC_ID = "clinic-001"


class Clinic:
    def __init__(self, clinic_id, name, clinician_id=None, patient_ids=None):
        self.clinic_id = clinic_id
        self.name = name
        self.clinician_id = clinician_id
        self.patient_ids = patient_ids or []

    def save(self):
        data = load_json(CLINICS_FILE)
        data[self.clinic_id] = {
            "name": self.name,
            "clinician_id": self.clinician_id,
            "patient_ids": self.patient_ids,
        }
        save_json(CLINICS_FILE, data)

    @staticmethod
    def get(clinic_id):
        return load_json(CLINICS_FILE).get(clinic_id)

    @staticmethod
    def get_or_create_default(clinician_id=None):
        """This starter ships a single shared clinic to keep the plumbing simple.

        For multiple clinics, extend registration to let a clinician create/select
        a clinic, and scope patient visibility to Clinic.patients_of(clinician_id)
        instead of "all patients" as the starter routes currently do.
        """
        data = load_json(CLINICS_FILE)
        record = data.get(DEFAULT_CLINIC_ID)
        if record is None:
            clinic = Clinic(DEFAULT_CLINIC_ID, "Default Clinic", clinician_id=clinician_id)
            clinic.save()
            return clinic
        if clinician_id and record.get("clinician_id") is None:
            record["clinician_id"] = clinician_id
            save_json(CLINICS_FILE, data)
        return Clinic(DEFAULT_CLINIC_ID, record["name"], record.get("clinician_id"),
                       record.get("patient_ids", []))

    @staticmethod
    def add_patient(clinic_id, patient_id):
        data = load_json(CLINICS_FILE)
        if clinic_id in data and patient_id not in data[clinic_id]["patient_ids"]:
            data[clinic_id]["patient_ids"].append(patient_id)
            save_json(CLINICS_FILE, data)
