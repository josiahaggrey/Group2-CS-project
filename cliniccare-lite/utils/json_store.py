"""Shared JSON read/write helpers used by every model's persistence layer."""
import json
import os


def load_json(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    """Overwrite the file at `path` with `data`.

    Opens in 'r+' rather than 'w' so the file handle is reused, then explicitly
    seeks to the start and truncates before writing. Skipping f.truncate() after
    f.seek(0) leaves trailing bytes from the previous (longer) content behind,
    which silently corrupts the file and raises a JSONDecodeError('Extra data')
    on the very next read.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        return
    with open(path, "r+") as f:
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
