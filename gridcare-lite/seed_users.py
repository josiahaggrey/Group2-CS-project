"""Create demo user accounts for GridCare-Lite (run once after db.py)."""
import bcrypt

from db import init_db

DEMO_USERS = [
    ("admin1", "Admin123!", "admin"),
    ("engineer1", "Engineer123!", "engineer"),
    ("tech1", "Tech123!", "technician"),
    ("cs1", "CustService123!", "customer_service"),
]


def seed(conn):
    cur = conn.cursor()
    for username, password, role in DEMO_USERS:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
    conn.commit()


if __name__ == "__main__":
    connection = init_db()
    seed(connection)
    print("Seeded demo users:")
    for username, password, role in DEMO_USERS:
        print(f"  {username} / {password}  ({role})")
    connection.close()
