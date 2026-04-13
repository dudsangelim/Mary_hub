from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import settings
from app.errors import error_response

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


async def save_upload_file(file: UploadFile, family_id: str, student_id: str) -> tuple[str, int]:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise error_response("UNSUPPORTED_FILE_TYPE", "Unsupported file type", {"mime_type": file.content_type}, 422)

    extension = ALLOWED_MIME_TYPES[file.content_type]
    relative_path = Path(str(family_id)) / str(student_id) / f"{uuid.uuid4()}{extension}"
    target_path = Path(settings.upload_dir) / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    async with aiofiles.open(target_path, "wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.upload_max_size_bytes:
                await output.close()
                os.remove(target_path)
                raise error_response(
                    "FILE_TOO_LARGE",
                    "Upload exceeds maximum allowed size",
                    {"max_size_mb": settings.upload_max_size_mb},
                    422,
                )
            await output.write(chunk)

    return str(relative_path), size
