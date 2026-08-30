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
    def all():
        return load_json(MESSAGES_FILE)

    @staticmethod
    def inbox_for(user_id):
        """Messages addressed directly to user_id, plus clinic-wide announcements."""
        data = load_json(MESSAGES_FILE)
        return {
            mid: m for mid, m in data.items()
            if m["recipient_id"] == user_id or m.get("broadcast")
        }

    @staticmethod
    def sent_by(user_id):
        """Direct (non-broadcast) messages this user sent - the "sent" half
        the original inbox never showed."""
        data = load_json(MESSAGES_FILE)
        return {mid: m for mid, m in data.items()
                if m["sender_id"] == user_id and not m.get("broadcast")}

    @staticmethod
    def contacts_for(user_id):
        """Distinct user IDs this user has exchanged a direct message with,
        most-recently-active first - the thread list for the inbox."""
        data = load_json(MESSAGES_FILE)
        last_activity = {}
        for message in data.values():
            if message.get("broadcast"):
                continue
            if message["sender_id"] == user_id:
                other = message["recipient_id"]
            elif message["recipient_id"] == user_id:
                other = message["sender_id"]
            else:
                continue
            if other not in last_activity or message["timestamp"] > last_activity[other]:
                last_activity[other] = message["timestamp"]
        return sorted(last_activity, key=lambda uid: last_activity[uid], reverse=True)

    @staticmethod
    def conversation(user_a, user_b):
        data = load_json(MESSAGES_FILE)
        return {
            mid: m for mid, m in data.items()
            if not m.get("broadcast") and {m["sender_id"], m["recipient_id"]} == {user_a, user_b}
        }

    @staticmethod
    def unread_count(user_id):
        """Everything in this user's inbox (direct + broadcast) not yet
        marked read - what the nav badge and the polling endpoint report."""
        data = load_json(MESSAGES_FILE)
        return sum(
            1 for m in data.values()
            if (m["recipient_id"] == user_id or m.get("broadcast")) and not m.get("read")
        )

    @staticmethod
    def mark_read(message_id):
        data = load_json(MESSAGES_FILE)
        if message_id in data:
            data[message_id]["read"] = True
            save_json(MESSAGES_FILE, data)

    @staticmethod
    def mark_conversation_read(user_id, contact_id):
        """Marks every message from contact_id to user_id as read - called
        when the user opens that conversation thread."""
        data = load_json(MESSAGES_FILE)
        changed = False
        for message in data.values():
            if (message["sender_id"] == contact_id and message["recipient_id"] == user_id
                    and not message.get("read")):
                message["read"] = True
                changed = True
        if changed:
            save_json(MESSAGES_FILE, data)
