from __future__ import annotations

from pathlib import Path

from bson import ObjectId
from fastapi import FastAPI, Request, Depends, HTTPException
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
from app.routes.groq import router as groq_router
from app.routes.mentors import router as mentors_router
from app.routes.profiles import router as profiles_router
from app.routes.requests import router as requests_router
from app.routes.stories import router as stories_router
from app.routes.users import router as users_router
from app.utils.errors import AppError, error_response
from app.utils.profile import is_capstone_profile_complete


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
    app.include_router(groq_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(profiles_router, prefix="/api")
    app.include_router(mentors_router, prefix="/api")
    app.include_router(requests_router, prefix="/api")
    app.include_router(stories_router, prefix="/api")

    root_dir = Path(__file__).resolve().parents[1]
    pages_dir = root_dir / "Pages"
    if pages_dir.exists():
        app.mount("/pages", StaticFiles(directory=str(pages_dir), html=True), name="pages")

    assets_dir = root_dir / "assests"
    bex_dir = root_dir / "bex"
    if assets_dir.exists():
        app.mount("/assests", StaticFiles(directory=str(assets_dir)), name="assests")

        @app.get("/")
        async def root():
            return page("landing.html")

        @app.get("/landing")
        async def landing_page():
            return page("landing.html")

        def page(path: str) -> FileResponse:
            return FileResponse(str(pages_dir / path))

        @app.get("/bex")
        async def bex_page(request: Request, db=Depends(get_db)):
            try:
                await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            return page("bex.html")

        if bex_dir.exists():
            @app.get("/bex/{asset_path:path}")
            async def bex_asset(asset_path: str):
                candidate = bex_dir / asset_path
                if candidate.exists():
                    return FileResponse(str(candidate))
                raise HTTPException(status_code=404, detail="Asset not found")

        async def redirect_if_incomplete(user: dict, db):
            if user.get("role") == "ADMIN":
                return None
            user_id = user.get("id")
            if not user_id or not ObjectId.is_valid(user_id):
                return RedirectResponse(url="/authentication")
            if not user.get("role_selected", False):
                return RedirectResponse(url="/onboarding/role")
            object_id = ObjectId(user_id)
            if user.get("role") == "MENTOR":
                doc = await db.mentor_profiles.find_one({"user_id": object_id})
                if not doc:
                    return RedirectResponse(url="/mentor/setup")
                if not doc.get("approved_by_admin", False):
                    return RedirectResponse(url="/mentor/pending")
                return None
            doc = await db.capstone_profiles.find_one({"user_id": object_id})
            if not is_capstone_profile_complete(doc):
                return RedirectResponse(url="/profile/setup")
            return None

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
                redirect = await redirect_if_incomplete(user, db)
                return redirect or RedirectResponse(url="/mentor/dashboard")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("dashboard.html")

        @app.get("/main_dashboard")
        async def main_dashboard_page():
            return page("main_dashboard.html")

        @app.get("/profile")
        async def profile_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("profile_view.html")

        @app.get("/profile/setup")
        async def profile_setup_page():
            return page("profile_setup.html")

        @app.get("/mentor/setup")
        async def mentor_setup_page():
            return page("mentor_setup.html")

        @app.get("/mentor/pending")
        async def mentor_pending_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            if user.get("role") != "MENTOR":
                return RedirectResponse(url="/dashboard")
            user_id = user.get("id")
            if not user_id or not ObjectId.is_valid(user_id):
                return RedirectResponse(url="/mentor/setup")
            doc = await db.mentor_profiles.find_one({"user_id": ObjectId(user_id)})
            if not doc:
                return RedirectResponse(url="/mentor/setup")
            if doc.get("approved_by_admin", False):
                return RedirectResponse(url="/mentor/dashboard")
            return page("mentor_pending.html")

        @app.get("/mentor/dashboard")
        async def mentor_dashboard_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            if user.get("role") != "MENTOR":
                return RedirectResponse(url="/dashboard")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("mentor_dashboard.html")

        @app.get("/mentor_dashboard")
        async def mentor_dashboard_alias(request: Request, db=Depends(get_db)):
            return await mentor_dashboard_page(request, db)

        @app.get("/mentor/emails")
        async def mentor_emails_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            if user.get("role") != "MENTOR":
                return RedirectResponse(url="/dashboard")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("mentor_emails.html")

        @app.get("/mentors")
        async def mentors_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("mentors.html")

        @app.get("/mentors/request")
        async def mentors_request_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("mentor_request.html")

        @app.get("/hackathons")
        async def hackathons_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("hackathons.html")

        @app.get("/mentor_request")
        async def mentors_request_alias():
            return page("mentor_request.html")

        @app.get("/requests")
        async def requests_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
            return page("notifs_request.html")

        @app.get("/requests/new")
        async def request_message_page(request: Request, db=Depends(get_db)):
            try:
                user = await get_current_user(request.cookies.get(ACCESS_COOKIE), db)
            except AppError:
                return RedirectResponse(url="/authentication")
            redirect = await redirect_if_incomplete(user, db)
            if redirect:
                return redirect
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

        @app.get("/admin/stories")
        async def admin_stories_page():
            return page("admin_stories.html")

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
                return FileResponse(
                    str(animation_path),
                    headers={"Cache-Control": "public, max-age=31536000, immutable"},
                )

        animation_one_path = root_dir / "animation1.reencoded.mp4"
        if animation_one_path.exists():
            @app.get("/assets/animation1.mp4")
            async def animation_one_asset():
                return FileResponse(
                    str(animation_one_path),
                    headers={"Cache-Control": "public, max-age=31536000, immutable"},
                )

        animation_nobg_path = root_dir / "nya_animation_nobg.mp4"
        if animation_nobg_path.exists():
            @app.get("/assets/nya_animation_nobg.mp4")
            async def animation_nobg_asset():
                return FileResponse(
                    str(animation_nobg_path),
                    headers={"Cache-Control": "public, max-age=31536000, immutable"},
                )

        logo_nobg_path = root_dir / "nya_logo_nobg.png"
        if logo_nobg_path.exists():
            @app.get("/assets/nya_logo_nobg.png")
            async def logo_nobg_asset():
                return FileResponse(str(logo_nobg_path))

        yooo_path = root_dir / "yooo.jpeg"
        if yooo_path.exists():
            @app.get("/assets/yooo.jpeg")
            async def yooo_asset():
                return FileResponse(str(yooo_path))

        yoda_path = root_dir / "yoda.jpeg"
        if yoda_path.exists():
            @app.get("/assets/yoda.jpeg")
            async def yoda_asset():
                return FileResponse(str(yoda_path))

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

        @app.get("/assets/{asset_path:path}")
        async def asset_fallback(asset_path: str):
            candidate = root_dir / asset_path
            if candidate.exists():
                return FileResponse(str(candidate))
            assets_candidate = root_dir / "assests" / asset_path
            if assets_candidate.exists():
                return FileResponse(str(assets_candidate))
            raise HTTPException(status_code=404, detail="Asset not found")

    @app.on_event("startup")
    async def on_startup():
        db = get_database()
        await create_indexes(db)

    return app


app = create_app()
