"""Covers utils/json_store.py - flagged in the requirements audit as a
priority target, since a regression here silently corrupts every model's
persistence layer at once."""
import json

from utils.json_store import load_json, save_json


def test_load_json_missing_file_returns_empty_dict(tmp_path):
    assert load_json(str(tmp_path / "does_not_exist.json")) == {}


def test_load_json_empty_file_returns_empty_dict(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("")
    assert load_json(str(path)) == {}


def test_save_then_load_round_trips(tmp_path):
    path = str(tmp_path / "data.json")
    save_json(path, {"a": 1, "b": {"nested": True}})
    assert load_json(path) == {"a": 1, "b": {"nested": True}}


def test_save_creates_parent_directory(tmp_path):
    path = str(tmp_path / "nested" / "dir" / "data.json")
    save_json(path, {"x": 1})
    assert load_json(path) == {"x": 1}


def test_overwriting_with_shorter_content_does_not_corrupt_the_file(tmp_path):
    """Regression test for the exact bug the module's own docstring warns
    about: writing shorter content into a file opened with 'r+' without
    truncating leaves trailing bytes from the previous, longer write,
    which corrupts the JSON. If save_json() ever loses its f.truncate()
    call, this test fails with a JSONDecodeError instead of a silent
    assertion failure - closer to how the bug actually manifests."""
    path = str(tmp_path / "data.json")
    save_json(path, {"very_long_key_name": "a fairly long value to pad this out"})
    save_json(path, {"a": 1})  # much shorter than what was there before

    with open(path) as f:
        raw = f.read()
    # A corrupted file has trailing garbage after the valid JSON object -
    # parse it directly (not via load_json) so a corruption surfaces as
    # the JSONDecodeError it actually is, not a value mismatch.
    assert json.loads(raw) == {"a": 1}


def test_repeated_round_trips_stay_consistent(tmp_path):
    path = str(tmp_path / "data.json")
    for i in range(5):
        save_json(path, {"iteration": i, "payload": "x" * i})
        assert load_json(path) == {"iteration": i, "payload": "x" * i}
