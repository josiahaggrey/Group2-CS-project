from datetime import datetime

from config import MESSAGES_FILE
from utils.json_store import load_json, save_json


class Message:
    def __init__(self, sender_id, recipient_id, content, broadcast=False):
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.timestamp = datetime.now().isoformat()
        self.read = False
        self.broadcast = broadcast

    def save(self):
        data = load_json(MESSAGES_FILE)
        next_id = max((int(k) for k in data.keys()), default=0) + 1
        message_id = str(next_id)
        data[message_id] = {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "read": self.read,
            "broadcast": self.broadcast,
        }
        save_json(MESSAGES_FILE, data)
        return message_id

    @staticmethod
    def inbox_for(user_id):
        """Messages addressed directly to user_id, plus clinic-wide announcements."""
        data = load_json(MESSAGES_FILE)
        return {
            mid: m for mid, m in data.items()
            if m["recipient_id"] == user_id or m.get("broadcast")
        }

    @staticmethod
    def conversation(user_a, user_b):
        data = load_json(MESSAGES_FILE)
        return {
            mid: m for mid, m in data.items()
            if not m.get("broadcast") and {m["sender_id"], m["recipient_id"]} == {user_a, user_b}
        }

    @staticmethod
    def mark_read(message_id):
        data = load_json(MESSAGES_FILE)
        if message_id in data:
            data[message_id]["read"] = True
            save_json(MESSAGES_FILE, data)
