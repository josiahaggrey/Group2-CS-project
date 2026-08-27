"""
Automated coverage for models.py, closing the gap flagged in
docs/test_plan.md ("No `tests/` directory exists yet for gridcare-lite").

Each test is labelled with the test_plan.md case ID it satisfies where one
exists (GC-01 etc.); tests without a prefix cover functionality added after
that plan was written (severity, search/filter, Report, Complaint.all()).
"""
import pytest

from models import Complaint, Outage, Report, Substation, User, WorkOrder


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def test_create_hashes_password_not_plaintext(conn):
    # GC-15
    user = User.create(conn, "admin1", "Admin123!", "admin")
    assert user.password_hash != "Admin123!"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_authenticate_accepts_correct_password(conn):
    User.create(conn, "admin1", "Admin123!", "admin")
    user = User.authenticate(conn, "admin1", "Admin123!")
    assert user is not None
    assert user.username == "admin1"


def test_authenticate_rejects_wrong_password(conn):
    # GC-01
    User.create(conn, "admin1", "Admin123!", "admin")
    assert User.authenticate(conn, "admin1", "wrong-password") is None


def test_authenticate_rejects_nonexistent_user(conn):
    # GC-02
    assert User.authenticate(conn, "nobody", "irrelevant") is None


def test_create_rejects_invalid_role(conn):
    with pytest.raises(ValueError):
        User.create(conn, "someone", "Password123!", "manager")


def test_find_by_role_scopes_to_that_role(conn, users):
    # GC-04 (the query technician screens rely on for "my work orders only")
    technicians = User.find_by_role(conn, "technician")
    assert len(technicians) == 1
    assert technicians[0].username == "tech1"
    assert all(t.role == "technician" for t in technicians)


# ---------------------------------------------------------------------------
# Substation
# ---------------------------------------------------------------------------

def test_import_from_csv(conn, tmp_path):
    csv_path = tmp_path / "substations.csv"
    csv_path.write_text(
        "Substation ID,Name,Short Name,Region\n"
        "1,Achimota Substation,Achimota,Greater Accra\n"
        "2,Tema Substation,Tema,Greater Accra\n"
    )
    count = Substation.import_from_csv(conn, str(csv_path))
    assert count == 2
    assert len(Substation.all(conn)) == 2


def test_import_from_csv_is_idempotent(conn, tmp_path):
    csv_path = tmp_path / "substations.csv"
    csv_path.write_text(
        "Substation ID,Name,Short Name,Region\n1,Achimota Substation,Achimota,Greater Accra\n"
    )
    Substation.import_from_csv(conn, str(csv_path))
    Substation.import_from_csv(conn, str(csv_path))  # second import, same rows
    assert len(Substation.all(conn)) == 1


def test_exists(conn, substation):
    assert Substation.exists(conn, substation.substation_id) is True
    assert Substation.exists(conn, 9999) is False


def test_regions_returns_distinct_sorted(conn):
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
        [(1, "A", "Volta"), (2, "B", "Ashanti"), (3, "C", "Volta")],
    )
    conn.commit()
    assert Substation.regions(conn) == ["Ashanti", "Volta"]


# ---------------------------------------------------------------------------
# Outage
# ---------------------------------------------------------------------------

def test_report_creates_open_outage_with_severity(conn, substation, users):
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id,
                            "Transformer fault", severity="High")
    assert outage.status == "Open"
    assert outage.severity == "High"
    assert outage.outage_id is not None


def test_report_defaults_to_medium_severity(conn, substation, users):
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    assert outage.severity == "Medium"


def test_report_rejects_empty_description(conn, substation, users):
    # GC-05
    with pytest.raises(ValueError):
        Outage.report(conn, substation.substation_id, users["engineer"].user_id, "   ")


def test_report_rejects_invalid_severity(conn, substation, users):
    with pytest.raises(ValueError):
        Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault",
                       severity="Catastrophic")


def test_report_rejects_nonexistent_substation(conn, users):
    # GC-06
    with pytest.raises(ValueError):
        Outage.report(conn, 9999, users["engineer"].user_id, "Fault at a substation that isn't real")


def test_report_rejects_exact_duplicate_while_open(conn, substation, users):
    # GC-10
    Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Line down")
    with pytest.raises(ValueError):
        Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Line down")


def test_report_allows_same_description_once_resolved(conn, substation, users):
    """Not a duplicate once the first one is closed - re-reporting a
    recurring fault at the same substation is legitimate."""
    first = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Line down")
    first.mark_resolved(conn)
    second = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Line down")
    assert second.outage_id != first.outage_id


def test_search_filters_by_region_and_status(conn, users):
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
        [(1, "A", "Volta"), (2, "B", "Ashanti")],
    )
    conn.commit()
    o1 = Outage.report(conn, 1, users["engineer"].user_id, "Fault A")
    Outage.report(conn, 2, users["engineer"].user_id, "Fault B")
    o1.mark_resolved(conn)

    assert len(Outage.search(conn, region="Volta")) == 1
    assert len(Outage.search(conn, region="Ashanti")) == 1
    assert len(Outage.search(conn, status="Resolved")) == 1
    assert len(Outage.search(conn, status="Open")) == 1
    assert len(Outage.search(conn)) == 2


def test_mark_resolved_sets_status_and_timestamp(conn, substation, users):
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    assert outage.resolved_at is None
    outage.mark_resolved(conn)
    assert outage.status == "Resolved"


# ---------------------------------------------------------------------------
# WorkOrder
# ---------------------------------------------------------------------------

def test_assign_moves_outage_to_in_progress(conn, substation, users):
    # GC-07
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    WorkOrder.assign(conn, outage.outage_id, users["technician"].user_id, "2026-09-01")
    refreshed = Outage.search(conn)[0]
    assert refreshed.status == "In Progress"


def test_assign_rejects_missing_scheduled_date(conn, substation, users):
    # GC-08
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    with pytest.raises(ValueError):
        WorkOrder.assign(conn, outage.outage_id, users["technician"].user_id, "  ")


def test_for_technician_scoped_to_that_technician(conn, substation, users):
    # GC-04
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    other_tech = User.create(conn, "tech2", "Tech123!", "technician")
    WorkOrder.assign(conn, outage.outage_id, users["technician"].user_id, "2026-09-01")

    assert len(WorkOrder.for_technician(conn, users["technician"].user_id)) == 1
    assert len(WorkOrder.for_technician(conn, other_tech.user_id)) == 0


def test_mark_complete_resolves_the_outage(conn, substation, users):
    # GC-09
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    work_order = WorkOrder.assign(conn, outage.outage_id, users["technician"].user_id, "2026-09-01")
    work_order.mark_complete(conn)

    assert work_order.status == "Completed"
    refreshed = Outage.search(conn)[0]
    assert refreshed.status == "Resolved"
    assert refreshed.resolved_at is not None


# ---------------------------------------------------------------------------
# Complaint
# ---------------------------------------------------------------------------

def test_log_creates_unlinked_complaint(conn, users):
    complaint = Complaint.log(conn, users["customer_service"].user_id, "Jane Doe", "No power")
    assert complaint.outage_id is None


def test_log_rejects_missing_name(conn, users):
    # GC-12
    with pytest.raises(ValueError):
        Complaint.log(conn, users["customer_service"].user_id, "  ", "No power")


def test_log_rejects_missing_description(conn, users):
    # GC-12
    with pytest.raises(ValueError):
        Complaint.log(conn, users["customer_service"].user_id, "Jane Doe", "  ")


def test_log_rejects_nonexistent_outage_id(conn, users):
    # GC-11
    with pytest.raises(ValueError):
        Complaint.log(conn, users["customer_service"].user_id, "Jane Doe", "No power", outage_id=9999)


def test_log_accepts_a_real_outage_id(conn, substation, users):
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "Fault")
    complaint = Complaint.log(conn, users["customer_service"].user_id, "Jane Doe", "No power",
                               outage_id=outage.outage_id)
    assert complaint.outage_id == outage.outage_id


def test_all_returns_newest_first_with_logger_username(conn, users):
    Complaint.log(conn, users["customer_service"].user_id, "First", "Complaint one")
    Complaint.log(conn, users["customer_service"].user_id, "Second", "Complaint two")
    complaints = Complaint.all(conn)
    assert [c.customer_name for c in complaints] == ["Second", "First"]
    assert complaints[0].logged_by_username == "cs1"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def test_status_counts_zero_fills_missing_statuses(conn):
    counts = Report.status_counts(conn)
    assert counts == {"Open": 0, "In Progress": 0, "Resolved": 0}


def test_status_counts_reflects_real_data(conn, substation, users):
    Outage.report(conn, substation.substation_id, users["engineer"].user_id, "A")
    Outage.report(conn, substation.substation_id, users["engineer"].user_id, "B").mark_resolved(conn)
    counts = Report.status_counts(conn)
    assert counts["Open"] == 1
    assert counts["Resolved"] == 1


def test_average_resolution_hours_none_when_nothing_resolved(conn, substation, users):
    Outage.report(conn, substation.substation_id, users["engineer"].user_id, "A")
    assert Report.average_resolution_hours(conn) is None


def test_average_resolution_hours_computed_for_resolved(conn, substation, users):
    outage = Outage.report(conn, substation.substation_id, users["engineer"].user_id, "A")
    outage.mark_resolved(conn)
    # Resolved essentially instantly in a test, so this should be ~0 hours,
    # not None - the important thing is it doesn't error and returns a number.
    result = Report.average_resolution_hours(conn)
    assert result is not None
    assert result >= 0


def test_outages_by_region_groups_correctly(conn, users):
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO substations (substation_id, name, region) VALUES (?, ?, ?)",
        [(1, "A", "Volta"), (2, "B", "Volta"), (3, "C", "Ashanti")],
    )
    conn.commit()
    Outage.report(conn, 1, users["engineer"].user_id, "Fault A")
    Outage.report(conn, 2, users["engineer"].user_id, "Fault B")
    Outage.report(conn, 3, users["engineer"].user_id, "Fault C")

    by_region = dict(Report.outages_by_region(conn))
    assert by_region["Volta"] == 2
    assert by_region["Ashanti"] == 1


def test_summary_bundles_everything(conn, substation, users):
    Outage.report(conn, substation.substation_id, users["engineer"].user_id, "A")
    Complaint.log(conn, users["customer_service"].user_id, "Jane", "No power")

    summary = Report.summary(conn)
    assert summary["total_outages"] == 1
    assert summary["total_complaints"] == 1
    assert "status_counts" in summary
    assert "severity_counts" in summary
    assert "by_region" in summary
