from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.utils.mongo import PyObjectId


class UserModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    email: str
    role: Literal["USER", "MENTOR", "ADMIN"]
    created_at: datetime
    last_login: datetime

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
