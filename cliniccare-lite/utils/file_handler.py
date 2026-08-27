"""File-handling helpers shared by upload routes and the TaskSubmission model."""
import os
import shutil

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, TASK_ATTACHMENTS_DIR


def is_allowed_extension(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def is_within_size_limit(file_path):
    return os.path.getsize(file_path) <= MAX_FILE_SIZE_BYTES


def save_task_attachment(task_id, source_path):
    """Copy a clinician-provided task attachment into TASK_ATTACHMENTS_DIR,
    named after the task so it's found the same way a submission is - one
    attachment per task, most recent one wins if re-uploaded. Raises
    ValueError on the same type/size rules as a patient submission."""
    if not is_allowed_extension(source_path):
        raise ValueError("Only .txt, .csv, and .pdf files are allowed.")
    if not is_within_size_limit(source_path):
        raise ValueError("File exceeds the maximum allowed size (5 MB).")

    ext = os.path.splitext(source_path)[1].lower()
    os.makedirs(TASK_ATTACHMENTS_DIR, exist_ok=True)
    dest_path = os.path.join(TASK_ATTACHMENTS_DIR, f"{task_id}{ext}")
    shutil.copy(source_path, dest_path)
    return dest_path
