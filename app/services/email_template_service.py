from __future__ import annotations

import html
from pathlib import Path

from app.utils.errors import AppError


class EmailTemplateService:
    def __init__(self) -> None:
        self._template_dir = Path(__file__).resolve().parents[1] / "templates"
        self._templates = {
            "request_created": {
                "name": "Team Request Created",
                "file": "email_request_created.html",
                "placeholders": ["recipient_name", "sender_name", "message", "cta_url", "profile_url"],
                "sample": {
                    "recipient_name": "Riya",
                    "sender_name": "Aarav",
                    "message": "Would you like to join our capstone team?",
                    "cta_url": "http://localhost:8000/requests",
                    "profile_url": "http://localhost:8000/profile?user_id=sample",
                },
            },
            "request_accepted": {
                "name": "Team Request Accepted",
                "file": "email_request_accepted.html",
                "placeholders": ["recipient_name", "accepter_name", "cta_url"],
                "sample": {
                    "recipient_name": "Aarav",
                    "accepter_name": "Riya",
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

    def get_template(self, template_id: str) -> dict:
        meta = self._get_meta(template_id)
        content = self._read_template(meta["file"])
        return {
            "id": template_id,
            "name": meta["name"],
            "placeholders": meta["placeholders"],
            "content": content,
        }

    def update_template(self, template_id: str, content: str) -> None:
        meta = self._get_meta(template_id)
        self._write_template(meta["file"], content)

    def render_preview(self, template_id: str, content: str | None = None) -> str:
        meta = self._get_meta(template_id)
        template = content if content is not None else self._read_template(meta["file"])
        return self._apply_context(template, meta["sample"])

    def _get_meta(self, template_id: str) -> dict:
        if template_id not in self._templates:
            raise AppError(404, "template_not_found", "Template not found")
        return self._templates[template_id]

    def _read_template(self, filename: str) -> str:
        path = self._template_dir / filename
        return path.read_text(encoding="utf-8")

    def _write_template(self, filename: str, content: str) -> None:
        path = self._template_dir / filename
        path.write_text(content, encoding="utf-8")

    def _apply_context(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            escaped = html.escape(value)
            if key == "message":
                escaped = escaped.replace("\n", "<br>")
            rendered = rendered.replace(f"{{{{{key}}}}}", escaped)
        return rendered
