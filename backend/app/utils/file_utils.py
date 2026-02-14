import os
from pathlib import Path
import uuid
import shutil
import os

def get_file_extension(file_path: str) -> str:
    return Path(file_path).suffix.lower()

async def save_file_locally(temp_dir: str, file) -> str:
    # Create temp directory if not exists
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

    # Save file locally for processing
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path