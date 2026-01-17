from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RequestCreate(BaseModel):
    to_user_id: str = Field(min_length=1)
    type: Literal["CAPSTONE", "MENTORSHIP"]
    message: str = Field(min_length=1, max_length=1000)


class RequestSummary(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    type: Literal["CAPSTONE", "MENTORSHIP"]
    message: str
    status: Literal["PENDING", "ACCEPTED", "REJECTED"]
    created_at: datetime


class RequestListItem(RequestSummary):
    counterpart_name: str
    counterpart_role: Literal["USER", "MENTOR", "ADMIN"]
    counterpart_email: str | None = None
