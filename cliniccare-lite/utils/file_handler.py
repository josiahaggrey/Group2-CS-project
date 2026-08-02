"""File-handling helpers shared by upload routes and the TaskSubmission model."""
import os

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def is_allowed_extension(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def is_within_size_limit(file_path):
    return os.path.getsize(file_path) <= MAX_FILE_SIZE_BYTES
