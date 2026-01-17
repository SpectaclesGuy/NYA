from __future__ import annotations

import asyncio
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.core.config import settings


class EmailService:
    def __init__(self) -> None:
        self._template_dir = Path(__file__).resolve().parents[1] / "templates"

    def _enabled(self) -> bool:
        return bool(settings.smtp_enabled and settings.smtp_user and settings.smtp_password)

    def _from_address(self) -> str:
        return settings.smtp_from or settings.smtp_user

    def _render_template(self, name: str, context: dict[str, str]) -> str:
        path = self._template_dir / name
        template = path.read_text(encoding="utf-8")
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", value)
        return template

    async def send_request_created(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        sender_name: str,
        message: str,
        cta_url: str,
        profile_url: str,
    ) -> None:
        if not self._enabled():
            return
        safe_message = html.escape(message or "").replace("\n", "<br>")
        html_body = self._render_template(
            "email_request_created.html",
            {
                "recipient_name": html.escape(recipient_name or "there"),
                "sender_name": html.escape(sender_name or "A NYA member"),
                "message": safe_message,
                "cta_url": html.escape(cta_url),
                "profile_url": html.escape(profile_url),
            },
        )
        subject = f"{sender_name} sent you a team request"
        await self._send_email(recipient_email, subject, html_body)

    async def send_request_accepted(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        accepter_name: str,
        cta_url: str,
    ) -> None:
        if not self._enabled():
            return
        html_body = self._render_template(
            "email_request_accepted.html",
            {
                "recipient_name": html.escape(recipient_name or "there"),
                "accepter_name": html.escape(accepter_name or "A NYA member"),
                "cta_url": html.escape(cta_url),
            },
        )
        subject = f"{accepter_name} accepted your request"
        await self._send_email(recipient_email, subject, html_body)

    async def send_mentor_request_created(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        sender_name: str,
        message: str,
        cta_url: str,
    ) -> None:
        if not self._enabled():
            return
        safe_message = html.escape(message or "").replace("\n", "<br>")
        html_body = self._render_template(
            "email_mentor_request_created.html",
            {
                "recipient_name": html.escape(recipient_name or "there"),
                "sender_name": html.escape(sender_name or "A NYA student"),
                "message": safe_message,
                "cta_url": html.escape(cta_url),
            },
        )
        subject = f"{sender_name} requested mentorship"
        await self._send_email(recipient_email, subject, html_body)

    async def send_mentor_request_accepted(
        self,
        *,
        recipient_email: str,
        recipient_name: str,
        mentor_name: str,
        cta_url: str,
    ) -> None:
        if not self._enabled():
            return
        html_body = self._render_template(
            "email_mentor_request_accepted.html",
            {
                "recipient_name": html.escape(recipient_name or "there"),
                "mentor_name": html.escape(mentor_name or "A NYA mentor"),
                "cta_url": html.escape(cta_url),
            },
        )
        subject = f"{mentor_name} accepted your mentorship request"
        await self._send_email(recipient_email, subject, html_body)

    async def send_custom_html(self, recipient_email: str, subject: str, html_body: str) -> None:
        if not self._enabled():
            return
        await self._send_email(recipient_email, subject, html_body)

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> None:
        await asyncio.to_thread(self._send_email_sync, to_email, subject, html_body)

    def _send_email_sync(self, to_email: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from_address()
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if settings.smtp_use_starttls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(msg["From"], [to_email], msg.as_string())
        else:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(msg["From"], [to_email], msg.as_string())
