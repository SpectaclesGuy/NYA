from __future__ import annotations

from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "nya_access"
REFRESH_COOKIE = "nya_refresh"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": settings.cookie_samesite,
        "domain": settings.cookie_domain,
        "path": "/",
    }
    response.set_cookie(key=ACCESS_COOKIE, value=access_token, max_age=settings.jwt_access_minutes * 60, **cookie_kwargs)
    response.set_cookie(key=REFRESH_COOKIE, value=refresh_token, max_age=settings.jwt_refresh_days * 86400, **cookie_kwargs)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=ACCESS_COOKIE, path="/", domain=settings.cookie_domain)
    response.delete_cookie(key=REFRESH_COOKIE, path="/", domain=settings.cookie_domain)
