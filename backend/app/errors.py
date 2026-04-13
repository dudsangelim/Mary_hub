from __future__ import annotations

from fastapi import HTTPException, status


def error_response(code: str, message: str, details: dict | None = None, http_status: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message, "details": details or {}})
