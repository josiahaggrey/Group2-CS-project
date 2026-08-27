"""
Covers app.py's guard_db_errors decorator (GC-13: database failures should
show a dialog, not crash the app) without needing a real Tk window - it
patches app.messagebox.showerror rather than instantiating any widget.
"""
import sqlite3

from app import guard_db_errors


def test_guard_db_errors_catches_sqlite_error_instead_of_raising(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.messagebox.showerror",
        lambda title, message: calls.append((title, message)),
    )

    @guard_db_errors
    def flaky():
        raise sqlite3.OperationalError("database is locked")

    result = flaky()

    assert result is None  # doesn't propagate - the caller's screen keeps running
    assert len(calls) == 1
    title, message = calls[0]
    assert title == "Database Error"
    assert "database is locked" in message


def test_guard_db_errors_lets_normal_returns_through(monkeypatch):
    monkeypatch.setattr("app.messagebox.showerror", lambda title, message: None)

    @guard_db_errors
    def works():
        return 42

    assert works() == 42


def test_guard_db_errors_does_not_swallow_other_exceptions(monkeypatch):
    """Only sqlite3.Error is a "database is unavailable" situation - a bug
    in the calling code (e.g. a TypeError) should still surface normally
    rather than being hidden behind the same generic dialog."""
    @guard_db_errors
    def buggy():
        raise TypeError("not a database problem")

    try:
        buggy()
    except TypeError:
        pass
    else:
        assert False, "expected TypeError to propagate, not be swallowed"
