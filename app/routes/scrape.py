from __future__ import annotations

import html
from pathlib import Path

import anyio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.core.dependencies import require_onboarding_complete
from app.services.email_service import EmailService
from app.services.instagram_scrape_service import InstagramScrapeResult, scrape_instagram_videos


router = APIRouter(prefix="/scrape", tags=["scrape"])


class InstagramScrapeRequest(BaseModel):
    target_username: str = Field(..., min_length=1)
    start_at_post_index: int = Field(default=0, ge=0)
    max_videos_to_process: int = Field(default=10, ge=1, le=5000)
    download_folder: str = Field(default="instagram_downloads")
    output_filename: str = Field(default="combined_transcripts.txt")
    delete_after_transcription: bool = True
    whisper_model: str = Field(default="base")
    recipient_email: EmailStr | None = None


@router.post("/instagram", response_model=InstagramScrapeResult)
async def scrape_instagram(
    payload: InstagramScrapeRequest,
    _current_user=Depends(require_onboarding_complete),
):
    result = await anyio.to_thread.run_sync(
        scrape_instagram_videos,
        payload.model_dump(),
        settings.instagram_username,
        settings.instagram_password,
    )

    if payload.recipient_email:
        email_service = EmailService()
        if not email_service.is_enabled():
            raise HTTPException(status_code=503, detail="SMTP is not configured for sending emails.")

        transcript_path = Path(result.output_filename)
        if not transcript_path.exists() or not transcript_path.is_file():
            raise HTTPException(status_code=500, detail="Transcript file was not found after scrape.")

        transcript_bytes = transcript_path.read_bytes()
        subject = f"Instagram transcript: {result.target_username}"
        html_body = (
            f"<p>Your transcript file is ready for "
            f"<strong>{html.escape(result.target_username)}</strong>.</p>"
            f"<p>Processed videos: {result.videos_processed}</p>"
        )
        await email_service.send_custom_html_with_attachment(
            recipient_email=str(payload.recipient_email),
            subject=subject,
            html_body=html_body,
            attachment_name=transcript_path.name,
            attachment_content=transcript_bytes,
            mime_type="text/plain",
        )
        result.recipient_email = str(payload.recipient_email)
        result.email_sent = True

    return result
