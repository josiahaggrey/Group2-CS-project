"""Covers utils/file_handler.py - extension/size gating for both patient
submissions and clinician task attachments, and the save_task_attachment
helper end to end."""
import pytest

from utils.file_handler import is_allowed_extension, is_within_size_limit, save_task_attachment


def test_allowed_extensions_accepted():
    assert is_allowed_extension("readings.csv") is True
    assert is_allowed_extension("notes.txt") is True
    assert is_allowed_extension("scan.pdf") is True


def test_disallowed_extension_rejected():
    assert is_allowed_extension("photo.jpg") is False
    assert is_allowed_extension("script.exe") is False
    assert is_allowed_extension("noextension") is False


def test_extension_check_is_case_insensitive():
    assert is_allowed_extension("READINGS.CSV") is True


def test_within_size_limit(tmp_path):
    small_file = tmp_path / "small.txt"
    small_file.write_bytes(b"x" * 100)
    assert is_within_size_limit(str(small_file)) is True


def test_exceeds_size_limit(tmp_path):
    big_file = tmp_path / "big.txt"
    big_file.write_bytes(b"x" * (6 * 1024 * 1024))  # 6 MB > the 5 MB limit
    assert is_within_size_limit(str(big_file)) is False


def test_save_task_attachment_copies_and_renames(tmp_path, monkeypatch):
    attachments_dir = str(tmp_path / "task_attachments")
    monkeypatch.setattr("utils.file_handler.TASK_ATTACHMENTS_DIR", attachments_dir)

    source = tmp_path / "intake_form.csv"
    source.write_text("field,value\nname,\n")

    dest_path = save_task_attachment("abc12345", str(source))

    assert dest_path.endswith("abc12345.csv")
    with open(dest_path) as f:
        assert f.read() == "field,value\nname,\n"


def test_save_task_attachment_rejects_bad_extension(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.file_handler.TASK_ATTACHMENTS_DIR", str(tmp_path / "task_attachments"))
    source = tmp_path / "malware.exe"
    source.write_bytes(b"not a real executable")

    with pytest.raises(ValueError):
        save_task_attachment("abc12345", str(source))


def test_save_task_attachment_rejects_oversized_file(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.file_handler.TASK_ATTACHMENTS_DIR", str(tmp_path / "task_attachments"))
    source = tmp_path / "huge.csv"
    source.write_bytes(b"x" * (6 * 1024 * 1024))

    with pytest.raises(ValueError):
        save_task_attachment("abc12345", str(source))
