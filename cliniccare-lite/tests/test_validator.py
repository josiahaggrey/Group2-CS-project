"""Covers utils/validator.py - ID format, password complexity, and the
structural form-completeness check. Flagged in the requirements audit as
the cheapest, highest-priority place to start automated coverage."""
from utils.validator import check_form_completeness, validate_id, validate_password


# ---------------------------------------------------------------------------
# validate_id
# ---------------------------------------------------------------------------

def test_clinician_id_ending_0000_is_valid():
    assert validate_id("12340000", "clinician") is True


def test_clinician_id_not_ending_0000_is_invalid():
    assert validate_id("12341234", "clinician") is False


def test_patient_id_with_valid_year_is_valid():
    assert validate_id("12342024", "patient") is True
    assert validate_id("12342022", "patient") is True
    assert validate_id("12342028", "patient") is True


def test_patient_id_with_year_out_of_range_is_invalid():
    assert validate_id("12342021", "patient") is False
    assert validate_id("12342029", "patient") is False


def test_id_must_be_exactly_8_digits():
    assert validate_id("1234000", "clinician") is False  # 7 digits
    assert validate_id("123400000", "clinician") is False  # 9 digits
    assert validate_id("1234abcd", "clinician") is False  # not digits


def test_unknown_role_is_invalid():
    assert validate_id("12340000", "manager") is False


# ---------------------------------------------------------------------------
# validate_password
# ---------------------------------------------------------------------------

def test_valid_password_accepted():
    assert validate_password("Password1!") is True


def test_password_too_short_rejected():
    assert validate_password("Pw1!") is False


def test_password_missing_uppercase_rejected():
    assert validate_password("password1!") is False


def test_password_missing_lowercase_rejected():
    assert validate_password("PASSWORD1!") is False


def test_password_missing_digit_rejected():
    assert validate_password("Password!") is False


def test_password_missing_special_character_rejected():
    assert validate_password("Password1") is False


# ---------------------------------------------------------------------------
# check_form_completeness
# ---------------------------------------------------------------------------

def test_csv_with_header_and_data_has_no_issues(tmp_path):
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text("date,value\n2026-08-01,120\n2026-08-02,118\n")
    assert check_form_completeness(str(csv_path)) == []


def test_csv_missing_header_flagged(tmp_path):
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text("\n2026-08-01,120\n")
    issues = check_form_completeness(str(csv_path))
    assert any("column headers" in issue for issue in issues)


def test_csv_header_only_no_data_flagged(tmp_path):
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text("date,value\n")
    issues = check_form_completeness(str(csv_path))
    assert any("no data rows" in issue for issue in issues)


def test_csv_with_empty_row_flagged(tmp_path):
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text("date,value\n2026-08-01,120\n,\n")
    issues = check_form_completeness(str(csv_path))
    assert any("Row 3" in issue for issue in issues)


def test_empty_file_flagged(tmp_path):
    for ext in (".csv", ".txt"):
        file_path = tmp_path / f"empty{ext}"
        file_path.write_text("")
        issues = check_form_completeness(str(file_path))
        assert any("empty" in issue.lower() for issue in issues)


def test_nonempty_txt_has_no_issues(tmp_path):
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("Blood pressure log for August.")
    assert check_form_completeness(str(txt_path)) == []


def test_pdf_gets_no_structural_check(tmp_path):
    """.pdf isn't parsed at all - the function must not raise, and must
    not fabricate an opinion about content it can't read."""
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")
    assert check_form_completeness(str(pdf_path)) == []


def test_never_interprets_clinical_meaning(tmp_path):
    """Scope-boundary regression test: a value that would be clinically
    alarming (e.g. a wildly out-of-range reading) must never produce an
    issue - the checker only looks at structure, never at what a number
    means."""
    csv_path = tmp_path / "readings.csv"
    csv_path.write_text("date,systolic\n2026-08-01,240\n")  # clinically severe, structurally fine
    assert check_form_completeness(str(csv_path)) == []
