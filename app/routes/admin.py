from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import require_admin, get_db
from app.schemas.admin import PendingMentor
from app.schemas.admin_users import AdminUserSummary, AdminUserUpdate
from app.schemas.common import MessageResponse
from app.schemas.email_template import (
    EmailTemplateDetail,
    EmailTemplatePreview,
    EmailTemplatePreviewRequest,
    EmailTemplateSummary,
    EmailTemplateUpdate,
)
from app.services.admin_user_service import AdminUserService
from app.services.email_template_service import EmailTemplateService
from app.services.mentor_profile_service import MentorProfileService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/mentors/pending", response_model=list[PendingMentor])
async def list_pending_mentors(_admin=Depends(require_admin), db=Depends(get_db)):
    service = MentorProfileService(db)
    return await service.list_pending()


@router.post("/mentors/{mentor_profile_id}/approve", response_model=MessageResponse)
async def approve_mentor(mentor_profile_id: str, _admin=Depends(require_admin), db=Depends(get_db)):
    service = MentorProfileService(db)
    await service.approve(mentor_profile_id)
    return {"message": "approved"}


@router.post("/mentors/{mentor_profile_id}/reject", response_model=MessageResponse)
async def reject_mentor(mentor_profile_id: str, _admin=Depends(require_admin), db=Depends(get_db)):
    service = MentorProfileService(db)
    await service.reject(mentor_profile_id)
    return {"message": "rejected"}


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(_admin=Depends(require_admin), db=Depends(get_db)):
    return await AdminUserService(db).list_users()


@router.post("/users/{user_id}", response_model=MessageResponse)
async def update_user(user_id: str, payload: AdminUserUpdate, _admin=Depends(require_admin), db=Depends(get_db)):
    await AdminUserService(db).update_user(user_id, payload.action)
    return {"message": "updated"}


@router.get("/email-templates", response_model=list[EmailTemplateSummary])
async def list_email_templates(_admin=Depends(require_admin)):
    return EmailTemplateService().list_templates()


@router.get("/email-templates/{template_id}", response_model=EmailTemplateDetail)
async def get_email_template(template_id: str, _admin=Depends(require_admin)):
    return EmailTemplateService().get_template(template_id)


@router.post("/email-templates/{template_id}", response_model=MessageResponse)
async def update_email_template(
    template_id: str, payload: EmailTemplateUpdate, _admin=Depends(require_admin)
):
    EmailTemplateService().update_template(template_id, payload.content)
    return {"message": "updated"}


@router.post("/email-templates/{template_id}/preview", response_model=EmailTemplatePreview)
async def preview_email_template(
    template_id: str, payload: EmailTemplatePreviewRequest, _admin=Depends(require_admin)
):
    html = EmailTemplateService().render_preview(template_id, payload.content)
    return {"id": template_id, "html": html}
