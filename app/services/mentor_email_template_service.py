from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId

from app.utils.errors import AppError


class MentorEmailTemplateService:
    def __init__(self, db):
        self.db = db
        self._template_dir = Path(__file__).resolve().parents[1] / "templates"
        self._templates = {
            "mentor_request_created": {
                "name": "Prefectship Request Created",
                "file": "email_mentor_request_created.html",
                "placeholders": ["recipient_name", "sender_name", "message", "cta_url"],
                "sample": {
                    "recipient_name": "Prefect",
                    "sender_name": "Aarav",
                    "message": "I'd love to get your guidance on my capstone.",
                    "cta_url": "http://localhost:8000/mentor/dashboard",
                },
            },
            "mentor_request_accepted": {
                "name": "Prefectship Request Accepted",
                "file": "email_mentor_request_accepted.html",
                "placeholders": ["recipient_name", "mentor_name", "cta_url"],
                "sample": {
                    "recipient_name": "Aarav",
                    "mentor_name": "Riya",
                    "cta_url": "http://localhost:8000/requests",
                },
            },
        }

    def list_templates(self) -> list[dict]:
        return [
            {
                "id": key,
                "name": meta["name"],
                "placeholders": meta["placeholders"],
            }
            for key, meta in self._templates.items()
        ]

    async def get_template(self, mentor_id: str, template_id: str) -> dict:
        meta = self._get_meta(template_id)
        content = await self._get_content(mentor_id, template_id, meta["file"])
        return {
            "id": template_id,
            "name": meta["name"],
            "placeholders": meta["placeholders"],
            "content": content,
        }

    async def update_template(self, mentor_id: str, template_id: str, content: str) -> None:
        meta = self._get_meta(template_id)
        await self._write_template(mentor_id, template_id, meta["file"], content)

    async def render_preview(self, mentor_id: str, template_id: str, content: str | None = None) -> str:
        meta = self._get_meta(template_id)
        template = content if content is not None else await self._get_content(mentor_id, template_id, meta["file"])
        return self._apply_context(template, meta["sample"])

    async def render_with_context(self, mentor_id: str, template_id: str, context: dict[str, str]) -> str:
        meta = self._get_meta(template_id)
        template = await self._get_content(mentor_id, template_id, meta["file"])
        return self._apply_context(template, context)

    def _get_meta(self, template_id: str) -> dict:
        if template_id not in self._templates:
            raise AppError(404, "template_not_found", "Template not found")
        return self._templates[template_id]

    async def _get_content(self, mentor_id: str, template_id: str, filename: str) -> str:
        doc = await self.db.mentor_email_templates.find_one(
            {"mentor_id": ObjectId(mentor_id), "template_id": template_id}
        )
        if doc and doc.get("content"):
            return doc["content"]
        return self._read_default(filename)

    async def _write_template(self, mentor_id: str, template_id: str, filename: str, content: str) -> None:
        now = datetime.now(tz=timezone.utc)
        await self.db.mentor_email_templates.update_one(
            {"mentor_id": ObjectId(mentor_id), "template_id": template_id},
            {"$set": {"content": content, "updated_at": now, "template_file": filename}},
            upsert=True,
        )

    def _read_default(self, filename: str) -> str:
        path = self._template_dir / filename
        return path.read_text(encoding="utf-8")

    def _apply_context(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            escaped = html.escape(value)
            if key == "message":
                escaped = escaped.replace("\n", "<br>")
            rendered = rendered.replace(f"{{{{{key}}}}}", escaped)
        return rendered
