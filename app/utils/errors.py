from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorPayload


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Any] = None):
        super().__init__(status_code=status_code, detail=ErrorPayload(code=code, message=message, details=details).model_dump())


def error_response(code: str, message: str, details: Optional[Any] = None) -> dict:
    return ErrorResponse(error=ErrorPayload(code=code, message=message, details=details)).model_dump()
