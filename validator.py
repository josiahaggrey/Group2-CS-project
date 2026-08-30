"""Automated form-completeness checking for .csv/.txt submissions.

This is purely structural validation (are fields present, are cells non-empty) -
it never interprets the clinical meaning of a submitted value. See the project's
scope boundary: ClinicCare-Lite is administrative/communication only.
"""
import csv
import re

ID_PATTERN = re.compile(r"^\d{8}$")


def check_form_completeness(file_path):
    issues = []
    lower = file_path.lower()

    if lower.endswith(".csv"):
        with open(file_path, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            return ["The file is empty."]
        header, data_rows = rows[0], rows[1:]
        if not any(cell.strip() for cell in header):
            issues.append("The file has no column headers.")
        if not data_rows:
            issues.append("The file has a header row but no data rows.")
        for i, row in enumerate(data_rows, start=2):
            if not any(cell.strip() for cell in row):
                issues.append(f"Row {i} is completely empty.")
    elif lower.endswith(".txt"):
        with open(file_path) as f:
            content = f.read().strip()
        if not content:
            issues.append("The file is empty.")
    # .pdf submissions are previewed and reviewed directly by the clinician;
    # no automated structural check is applied.
    return issues


def validate_id(user_id, role):
    if not ID_PATTERN.match(user_id):
        return False
    if role == "clinician":
        return user_id[-4:] == "0000"
    if role == "patient":
        return 2022 <= int(user_id[-4:]) <= 2028
    return False


def validate_password(password):
    return bool(
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[!@#$%^&*]", password)
    )
