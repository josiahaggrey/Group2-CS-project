# Class Diagram — ClinicCare-Lite

Matches `models/*.py`. Every class owns its own JSON persistence
(`load_json`/`save_json` from `utils/json_store.py`) and behaviour;
`app.py` routes only handle HTTP input/output and call these methods.

```mermaid
classDiagram
    class User {
        +str user_id
        +str name
        +str email
        +str password "bcrypt hash"
        +str role "clinician / patient"
        +str theme
        +int engagement_points
        +check_password(password) bool
        +save()
        +exists(user_id)$ bool
        +get(user_id)$ User
        +all_by_role(role)$ dict
        +set_theme(user_id, theme)$
        +add_engagement_points(user_id, delta)$
        +validate_id(user_id, role)$ bool
        +validate_password(password)$ bool
    }

    class Clinic {
        +str clinic_id
        +str name
        +str clinician_id
        +list patient_ids
        +save()
        +get(clinic_id)$ dict
        +get_or_create_default(clinician_id)$ Clinic
        +add_patient(clinic_id, patient_id)$
    }

    class HealthTask {
        +str task_id
        +str title
        +str description
        +str due_date
        +str clinic_id
        +str assigned_patient_id
        +str created_by
        +save()
        +all()$ dict
        +get(task_id)$ dict
        +for_patient(patient_id)$ dict
        +for_clinician(clinician_id)$ dict
    }

    class TaskSubmission {
        +str patient_id
        +str task_id
        +str source_file_path
        +str file_path
        +str timestamp
        +str review_status "Pending / Reviewed-Normal / Needs Follow-up / Escalated"
        +str notes
        +str reviewer_id
        +str reviewed_at
        +validate_file() tuple
        +save_file()
        +save() str
        +all()$ dict
        +for_patient(patient_id)$ dict
        +review(key, reviewer_id, outcome, notes)$
    }

    class Message {
        +str sender_id
        +str recipient_id
        +str content
        +str timestamp
        +bool read
        +bool broadcast
        +save() str
        +inbox_for(user_id)$ dict
        +conversation(user_a, user_b)$ dict
        +mark_read(message_id)$
    }

    Clinic "1" --> "0..1" User : clinician
    Clinic "1" --> "0..*" User : patients
    User "1" --> "0..*" HealthTask : creates (clinician)
    User "1" --> "0..*" HealthTask : assigned (patient)
    HealthTask "1" --> "0..*" TaskSubmission : receives
    User "1" --> "0..*" TaskSubmission : submits (patient)
    User "1" --> "0..*" TaskSubmission : reviews (clinician)
    User "1" --> "0..*" Message : sends/receives
```

## Notes

- **No numeric grade.** `TaskSubmission.review_status` is one of four
  categorical outcomes (`config.REVIEW_OUTCOMES`), never a 0-100 score — see
  the course spec's explicit requirement that health data get administrative
  triage, not a grade.
- **Engagement Points are private by construction.** `add_engagement_points`
  only ever mutates the calling patient's own record; there is no method
  that reads or ranks points across patients (no leaderboard route exists in
  `app.py`).
- **`TaskSubmission.save_file()` validates before touching the filesystem.**
  Extension and size are checked (`validate_file`) before the file is copied
  into `submissions/<patient_id>/`, so a rejected upload never reaches disk.
- **Single shared `Clinic`** — `get_or_create_default()` is a known
  simplification; see `cliniccare-lite/README.md`'s "Known simplification"
  section for the multi-clinic extension path.
