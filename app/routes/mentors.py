from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_db
from app.schemas.mentor import (
    MentorDetail,
    MentorEmailTemplateDetail,
    MentorEmailTemplatePreview,
    MentorEmailTemplatePreviewRequest,
    MentorEmailTemplateSummary,
    MentorEmailTemplateUpdate,
    MentorSummary,
)
from app.schemas.mentor_setup import MentorMeResponse, MentorUpsertRequest
from app.services.mentor_profile_service import MentorProfileService
from app.services.mentor_email_template_service import MentorEmailTemplateService
from app.services.mentor_service import MentorService
from app.utils.errors import AppError

router = APIRouter(prefix="/mentors", tags=["mentors"])


@router.get("/me", response_model=MentorMeResponse)
async def get_my_mentor_profile(current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Only mentors can access mentor profile")
    service = MentorProfileService(db)
    return await service.get_my_profile(current_user["id"])


@router.post("/me", response_model=MentorMeResponse)
async def upsert_my_mentor_profile(
    payload: MentorUpsertRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Only mentors can update mentor profile")
    service = MentorProfileService(db)
    return await service.upsert_my_profile(
        user_id=current_user["id"],
        domain=payload.domain,
        experience_years=payload.experience_years,
        expertise=payload.expertise,
        links=payload.links,
        bio=payload.bio,
        availability=payload.availability,
    )


@router.get("", response_model=list[MentorSummary])
async def list_mentors(
    domain: str | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = MentorService(db)
    mentors = await service.list_mentors(domain=domain, search=search)
    return [
        {k: v for k, v in mentor.items() if k != "approved_by_admin"}
        for mentor in mentors
    ]


@router.get("/email-templates", response_model=list[MentorEmailTemplateSummary])
async def list_mentor_email_templates(current_user=Depends(get_current_user), db=Depends(get_db)):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Prefect access required")
    return MentorEmailTemplateService(db).list_templates()


@router.get("/email-templates/{template_id}", response_model=MentorEmailTemplateDetail)
async def get_mentor_email_template(
    template_id: str, current_user=Depends(get_current_user), db=Depends(get_db)
):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Prefect access required")
    service = MentorEmailTemplateService(db)
    return await service.get_template(current_user["id"], template_id)


@router.post("/email-templates/{template_id}", response_model=dict)
async def update_mentor_email_template(
    template_id: str,
    payload: MentorEmailTemplateUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Prefect access required")
    service = MentorEmailTemplateService(db)
    await service.update_template(current_user["id"], template_id, payload.content)
    return {"message": "updated"}


@router.post("/email-templates/{template_id}/preview", response_model=MentorEmailTemplatePreview)
async def preview_mentor_email_template(
    template_id: str,
    payload: MentorEmailTemplatePreviewRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    if current_user.get("role") != "MENTOR":
        raise AppError(403, "forbidden", "Prefect access required")
    service = MentorEmailTemplateService(db)
    html = await service.render_preview(current_user["id"], template_id, payload.content)
    return {"id": template_id, "html": html}


@router.get("/{mentor_id}", response_model=MentorDetail)
async def get_mentor(mentor_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    service = MentorService(db)
    return await service.get_mentor(mentor_id)
