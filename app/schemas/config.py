from __future__ import annotations

from pydantic import BaseModel


class PublicConfig(BaseModel):
    google_client_id: str
