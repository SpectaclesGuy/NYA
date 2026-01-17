from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.mongo import PyObjectId


class RequestModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    from_user_id: PyObjectId
    to_user_id: PyObjectId
    type: Literal["CAPSTONE", "MENTORSHIP"]
    message: str
    status: Literal["PENDING", "ACCEPTED", "REJECTED"]
    created_at: datetime

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
