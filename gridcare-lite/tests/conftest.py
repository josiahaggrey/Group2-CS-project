"""
Shared pytest fixtures for the gridcare-lite test suite.

Puts the component's own directory on sys.path (its modules are flat
files, not a package - `db.py`, `models.py`, `app.py` - matching how
gridcare-lite is actually run: `python app.py` from inside the folder).
Every test gets a fresh in-memory SQLite database via the real
db.init_db(), so tests exercise the actual schema (including the
severity-column migration path) rather than a hand-rolled substitute.
"""
import os
import sys

import pytest

GRIDCARE_LITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GRIDCARE_LITE_DIR)

from db import init_db  # noqa: E402
from models import Substation, User  # noqa: E402


@pytest.fixture
def conn():
    """A fresh in-memory database per test - no state leaks between tests,
    and nothing touches the real gridcare.db a developer might have open."""
    connection = init_db(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def substation(conn):
    """One reference substation, inserted directly (bypassing the CSV
    import path, which is covered separately) so outage tests have a
    valid substation_id to report against."""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
        (1, "Achimota Substation", "Greater Accra"),
    )
    conn.commit()
    return Substation(1, "Achimota Substation", "Greater Accra")


@pytest.fixture
def users(conn):
    """One user per role, matching seed_users.py's demo accounts."""
    roles = {
        "admin": ("admin1", "Admin123!"),
        "engineer": ("engineer1", "Engineer123!"),
        "technician": ("tech1", "Tech123!"),
        "customer_service": ("cs1", "CustService123!"),
    }
    created = {}
    for role, (username, password) in roles.items():
        created[role] = User.create(conn, username, password, role)
    return created
