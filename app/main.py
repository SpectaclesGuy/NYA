from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.core.security import ACCESS_COOKIE
from app.db.client import get_database
from app.db.indexes import create_indexes
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.onboarding import router as onboarding_router
from app.routes.config import router as config_router
from app.routes.mentors import router as mentors_router
from app.routes.profiles import router as profiles_router
from app.routes.requests import router as requests_router
from app.routes.users import router as users_router
from app.utils.errors import AppError, error_response


def create_app() -> FastAPI:
    app = FastAPI(title="NYA Backend", version="1.0.0")

    if settings.frontend_origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[settings.frontend_origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response("validation_error", "Invalid request", exc.errors()),
        )

    @app.exception_handler(Exception)
    async def default_handler(_request: Request, _exc: Exception):
        return JSONResponse(status_code=500, content=error_response("server_error", "Internal server error"))

    app.include_router(auth_router, prefix="/api")
    app.include_router(onboarding_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(config_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(profiles_router, prefix="/api")
    app.include_router(mentors_router, prefix="/api")
    app.include_router(requests_router, prefix="/api")

    root_dir = Path(__file__).resolve().parents[1]
    pages_dir = root_dir / "Pages"
    if pages_dir.exists():
        app.mount("/pages", StaticFiles(directory=str(pages_dir), html=True), name="pages")

        @app.get("/")
        async def root():
            return RedirectResponse(url="/authentication")

        def page(path: str) -> FileResponse:
            return FileResponse(str(pages_dir / path))

        @app.get("/authentication")
        async def authentication_page():
            return page("authentication.html")

        @app.get("/onboarding/role")
        async def role_selection_page():
            return page("role_selection.html")

        @app.get("/dashboard")
        async def dashboard_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            if user.get("role") == "MENTOR":
                return RedirectResponse(url="/mentor/dashboard")
            return page("dashboard.html")

        @app.get("/profile")
        async def profile_page():
            return page("profile_view.html")

        @app.get("/profile/setup")
        async def profile_setup_page():
            return page("profile_setup.html")

        @app.get("/mentor/setup")
        async def mentor_setup_page():
            return page("mentor_setup.html")

        @app.get("/mentor/pending")
        async def mentor_pending_page():
            return page("mentor_pending.html")

        @app.get("/mentor/dashboard")
        async def mentor_dashboard_page():
            return page("mentor_dashboard.html")

        @app.get("/mentor_dashboard")
        async def mentor_dashboard_alias():
            return page("mentor_dashboard.html")

        @app.get("/mentor/emails")
        async def mentor_emails_page():
            return page("mentor_emails.html")

        @app.get("/mentors")
        async def mentors_page():
            return page("mentors.html")

        @app.get("/mentors/request")
        async def mentors_request_page():
            return page("mentor_request.html")

        @app.get("/mentor_request")
        async def mentors_request_alias():
            return page("mentor_request.html")

        @app.get("/requests")
        async def requests_page():
            return page("notifs_request.html")

        @app.get("/requests/new")
        async def request_message_page():
            return page("request_message.html")

        @app.get("/transition")
        async def transition_page():
            return page("transition.html")

        @app.get("/admin/mentors")
        async def admin_mentors_page():
            return page("admin_mentors.html")

        @app.get("/admin/users")
        async def admin_users_page():
            return page("admin_users.html")

        @app.get("/admin/emails")
        async def admin_emails_page():
            return page("admin_emails.html")

        logo_path = root_dir / "nya_logo.png"
        if logo_path.exists():
            @app.get("/assets/nya_logo.png")
            async def logo_asset():
                return FileResponse(str(logo_path))

        favicon_path = root_dir / "logo.png"
        if favicon_path.exists():
            @app.get("/assets/logo.png")
            async def favicon_asset():
                return FileResponse(str(favicon_path))

        animation_path = root_dir / "animation.mp4"
        if animation_path.exists():
            @app.get("/assets/animation.mp4")
            async def animation_asset():
                return FileResponse(str(animation_path))

        animation_one_path = root_dir / "animation1.mp4"
        if animation_one_path.exists():
            @app.get("/assets/animation1.mp4")
            async def animation_one_asset():
                return FileResponse(str(animation_one_path))

        animation_nobg_path = root_dir / "nya_animation_nobg.mp4"
        if animation_nobg_path.exists():
            @app.get("/assets/nya_animation_nobg.mp4")
            async def animation_nobg_asset():
                return FileResponse(str(animation_nobg_path))

        logo_nobg_path = root_dir / "nya_logo_nobg.png"
        if logo_nobg_path.exists():
            @app.get("/assets/nya_logo_nobg.png")
            async def logo_nobg_asset():
                return FileResponse(str(logo_nobg_path))

        avatar_path = root_dir / "default_avatar.svg"
        if avatar_path.exists():
            @app.get("/assets/default_avatar.svg")
            async def avatar_asset():
                return FileResponse(str(avatar_path))

        avatar_two_path = root_dir / "default_avatar_2.svg"
        if avatar_two_path.exists():
            @app.get("/assets/default_avatar_2.svg")
            async def avatar_two_asset():
                return FileResponse(str(avatar_two_path))

        avatar_three_path = root_dir / "default_avatar_3.svg"
        if avatar_three_path.exists():
            @app.get("/assets/default_avatar_3.svg")
            async def avatar_three_asset():
                return FileResponse(str(avatar_three_path))

        avatar_four_path = root_dir / "default_avatar_4.svg"
        if avatar_four_path.exists():
            @app.get("/assets/default_avatar_4.svg")
            async def avatar_four_asset():
                return FileResponse(str(avatar_four_path))

        avatar_five_path = root_dir / "default_avatar_5.svg"
        if avatar_five_path.exists():
            @app.get("/assets/default_avatar_5.svg")
            async def avatar_five_asset():
                return FileResponse(str(avatar_five_path))

        avatar_six_path = root_dir / "default_avatar_6.svg"
        if avatar_six_path.exists():
            @app.get("/assets/default_avatar_6.svg")
            async def avatar_six_asset():
                return FileResponse(str(avatar_six_path))

        avatar_seven_path = root_dir / "default_avatar_7.svg"
        if avatar_seven_path.exists():
            @app.get("/assets/default_avatar_7.svg")
            async def avatar_seven_asset():
                return FileResponse(str(avatar_seven_path))

        avatar_eight_path = root_dir / "default_avatar_8.svg"
        if avatar_eight_path.exists():
            @app.get("/assets/default_avatar_8.svg")
            async def avatar_eight_asset():
                return FileResponse(str(avatar_eight_path))

        avatar_nine_path = root_dir / "default_avatar_9.svg"
        if avatar_nine_path.exists():
            @app.get("/assets/default_avatar_9.svg")
            async def avatar_nine_asset():
                return FileResponse(str(avatar_nine_path))

    @app.on_event("startup")
    async def on_startup():
        db = get_database()
        await create_indexes(db)

    return app


app = create_app()
