"""Create demo user accounts for GridCare-Lite (run once after db.py)."""
from db import init_db
from models import User

DEMO_USERS = [
    ("admin1", "Admin123!", "admin"),
    ("engineer1", "Engineer123!", "engineer"),
    ("tech1", "Tech123!", "technician"),
    ("cs1", "CustService123!", "customer_service"),
]


def seed(conn):
    for username, password, role in DEMO_USERS:
        if User.find_by_username(conn, username) is None:
            User.create(conn, username, password, role)


if __name__ == "__main__":
    connection = init_db()
    seed(connection)
    print("Seeded demo users:")
    for username, password, role in DEMO_USERS:
        print(f"  {username} / {password}  ({role})")
    connection.close()
