"""Database schema and initialisation for GridCare-Lite."""
import sqlite3

DB_PATH = "gridcare.db"


def _add_column_if_missing(conn, table, column, coldef):
    """SQLite's CREATE TABLE IF NOT EXISTS is a no-op on a table that
    already exists, so a schema change (like adding `severity`) needs an
    explicit migration for anyone with an existing gridcare.db from before
    this column existed - otherwise their app crashes on the first query
    that references it."""
    cur = conn.cursor()
    existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
        conn.commit()


def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'engineer', 'technician', 'customer_service'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS substations (
            substation_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS outages (
            outage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            substation_id INTEGER NOT NULL,
            reported_by INTEGER NOT NULL,
            description TEXT,
            severity TEXT NOT NULL DEFAULT 'Medium' CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
            status TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
            reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            FOREIGN KEY (substation_id) REFERENCES substations(substation_id),
            FOREIGN KEY (reported_by) REFERENCES users(user_id)
        )
    """)
    # Migration path for a gridcare.db created before `severity` existed.
    _add_column_if_missing(
        conn, "outages", "severity",
        "severity TEXT NOT NULL DEFAULT 'Medium' CHECK (severity IN ('Low', 'Medium', 'High', 'Critical'))",
    )

    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outage_id INTEGER NOT NULL,
            assigned_technician INTEGER,
            scheduled_date TEXT,
            status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'Completed')),
            FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
            FOREIGN KEY (assigned_technician) REFERENCES users(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            outage_id INTEGER,
            logged_by INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            description TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
            FOREIGN KEY (logged_by) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    return conn


if __name__ == "__main__":
    connection = init_db()
    print(f"Initialised database at {DB_PATH}")
    connection.close()
