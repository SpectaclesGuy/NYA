from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Response

from app.core.security import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.config import settings
from app.schemas.auth import AuthResponse, DevLoginRequest, GoogleLoginRequest
from app.services.auth_service import AuthService
from app.utils.errors import AppError
from app.core.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google/login", response_model=AuthResponse)
async def google_login(payload: GoogleLoginRequest, response: Response, db=Depends(get_db)):
    auth = AuthService(db)
    result = await auth.login_with_google(payload.id_token)
    set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return {"user": result["user"]}


# @router.post("/dev-login", response_model=AuthResponse)
# async def dev_login(payload: DevLoginRequest, response: Response, db=Depends(get_db)):
#     if not settings.dev_login_enabled:
#         raise AppError(404, "not_found", "Endpoint not available")
#     auth = AuthService(db)
#     result = await auth.dev_login(payload.email, payload.name)
#     set_auth_cookies(response, result["access_token"], result["refresh_token"])
#     return {"user": result["user"]}


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db=Depends(get_db),
):
    if not refresh_token:
        raise AppError(401, "refresh_required", "Refresh token required")
    auth = AuthService(db)
    result = await auth.refresh_tokens(refresh_token)
    set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return {"user": result["user"]}


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "logged_out"}
