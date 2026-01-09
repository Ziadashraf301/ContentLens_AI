import os
from pathlib import Path

def get_file_extension(file_path: str) -> str:
    return Path(file_path).suffix.lower()

def ensure_dir(directory: str):
    """Ensures a directory exists, creates it if not."""
    if not os.path.exists(directory):
        os.makedirs(directory)