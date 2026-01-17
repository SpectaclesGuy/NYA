from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_db
from app.schemas.request import RequestCreate, RequestListItem, RequestSummary
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestSummary)
async def create_request(payload: RequestCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    service = RequestService(db)
    return await service.create_request(
        from_user=current_user,
        to_user_id=payload.to_user_id,
        request_type=payload.type,
        message=payload.message,
    )


@router.get("/incoming", response_model=list[RequestListItem])
async def incoming_requests(current_user=Depends(get_current_user), db=Depends(get_db)):
    service = RequestService(db)
    return await service.list_incoming(current_user["id"])


@router.get("/outgoing", response_model=list[RequestListItem])
async def outgoing_requests(current_user=Depends(get_current_user), db=Depends(get_db)):
    service = RequestService(db)
    return await service.list_outgoing(current_user["id"])


@router.post("/{request_id}/accept", response_model=RequestSummary)
async def accept_request(request_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    service = RequestService(db)
    return await service.accept_request(request_id, current_user["id"])


@router.post("/{request_id}/reject", response_model=RequestSummary)
async def reject_request(request_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    service = RequestService(db)
    return await service.reject_request(request_id, current_user["id"])
