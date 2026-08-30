import bcrypt

from config import USERS_FILE
from utils.json_store import load_json, save_json
from utils.validator import validate_id, validate_password


class User:
    def __init__(self, user_id, name, email, password, role, theme=None,
                 hashed=False, engagement_points=0):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = (password if hashed else
                          bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"))
        self.role = role
        self.theme = theme or ("dark" if role == "clinician" else "colorful")
        self.engagement_points = engagement_points

    # ID and password rules live in utils.validator; exposed here for a
    # convenient User.validate_id(...) / User.validate_password(...) call site.
    validate_id = staticmethod(validate_id)
    validate_password = staticmethod(validate_password)

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))

    def save(self):
        data = load_json(USERS_FILE)
        data[self.user_id] = {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "theme": self.theme,
            "engagement_points": self.engagement_points,
        }
        save_json(USERS_FILE, data)

    @staticmethod
    def exists(user_id):
        return user_id in load_json(USERS_FILE)

    @staticmethod
    def get(user_id):
        record = load_json(USERS_FILE).get(user_id)
        if record is None:
            return None
        return User(
            user_id, record["name"], record["email"], record["password"], record["role"],
            theme=record.get("theme"), hashed=True,
            engagement_points=record.get("engagement_points", 0),
        )

    @staticmethod
    def all_by_role(role):
        return {uid: u for uid, u in load_json(USERS_FILE).items() if u["role"] == role}

    @staticmethod
    def set_theme(user_id, theme):
        data = load_json(USERS_FILE)
        if user_id in data:
            data[user_id]["theme"] = theme
            save_json(USERS_FILE, data)

    @staticmethod
    def add_engagement_points(user_id, delta):
        """Increment a patient's private Engagement Points.

        Never aggregated or compared across patients - visible only to the
        patient who earned them (see the patient dashboard / engagement route).
        """
        data = load_json(USERS_FILE)
        if user_id in data:
            data[user_id]["engagement_points"] = data[user_id].get("engagement_points", 0) + delta
            save_json(USERS_FILE, data)
