from pathlib import Path
from uuid import uuid4

from app.core.config import settings


def ensure_upload_dir() -> Path:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings.upload_dir


def save_upload(content: bytes, original_filename: str) -> str:
    upload_dir = ensure_upload_dir()
    suffix = Path(original_filename).suffix.lower() or ".pdf"
    stored_name = f"{uuid4()}{suffix}"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(content)
    return str(stored_path)


def delete_upload(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()
