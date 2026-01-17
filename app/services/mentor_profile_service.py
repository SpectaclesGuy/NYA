from __future__ import annotations

from bson import ObjectId

from app.core.config import settings
from app.services.email_service import EmailService
from app.utils.errors import AppError
from app.utils.mongo import normalize_id


class MentorProfileService:
    def __init__(self, db):
        self.db = db
        self.email_service = EmailService()

    async def get_my_profile(self, user_id: str) -> dict:
        doc = await self.db.mentor_profiles.find_one({"user_id": ObjectId(user_id)})
        if not doc:
            raise AppError(404, "mentor_profile_not_found", "Prefect profile not found")
        profile = normalize_id(doc)
        return {
            "user_id": str(profile["user_id"]),
            "domain": profile.get("domain", ""),
            "experience_years": profile.get("experience_years", 0),
            "expertise": profile.get("expertise", []),
            "links": profile.get("links", []),
            "bio": profile.get("bio", ""),
            "availability": profile.get("availability", ""),
            "approved_by_admin": profile.get("approved_by_admin", False),
        }

    async def upsert_my_profile(
        self,
        user_id: str,
        domain: str,
        experience_years: int,
        expertise: list[str],
        links: list[str],
        bio: str,
        availability: str,
    ) -> dict:
        cleaned_expertise = [skill.strip() for skill in expertise if skill.strip()]
        cleaned_links = [link.strip() for link in links if link.strip()]
        await self.db.mentor_profiles.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$set": {
                    "user_id": ObjectId(user_id),
                    "domain": domain,
                    "experience_years": experience_years,
                    "expertise": cleaned_expertise,
                    "links": cleaned_links,
                    "bio": bio,
                    "availability": availability,
                    "approved_by_admin": False,
                }
            },
            upsert=True,
        )
        profile = await self.get_my_profile(user_id)
        await self._notify_admin_mentor_application(user_id, profile)
        return profile

    async def list_pending(self) -> list[dict]:
        cursor = self.db.mentor_profiles.find({"approved_by_admin": False})
        results = []
        async for doc in cursor:
            profile = normalize_id(doc)
            user = await self.db.users.find_one({"_id": profile["user_id"]})
            if not user:
                continue
            results.append(
                {
                    "id": profile["id"],
                    "user_id": str(profile["user_id"]),
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "domain": profile.get("domain", ""),
                    "experience_years": profile.get("experience_years", 0),
                    "expertise": profile.get("expertise", []),
                    "links": profile.get("links", []),
                    "bio": profile.get("bio", ""),
                    "availability": profile.get("availability", ""),
                }
            )
        return results

    async def approve(self, mentor_profile_id: str) -> None:
        if not ObjectId.is_valid(mentor_profile_id):
            raise AppError(400, "invalid_mentor_id", "Invalid mentor id")
        await self.db.mentor_profiles.update_one(
            {"_id": ObjectId(mentor_profile_id)},
            {"$set": {"approved_by_admin": True}},
        )
        await self._notify_mentor_application_approved(mentor_profile_id)

    async def reject(self, mentor_profile_id: str) -> None:
        if not ObjectId.is_valid(mentor_profile_id):
            raise AppError(400, "invalid_mentor_id", "Invalid mentor id")
        await self.db.mentor_profiles.update_one(
            {"_id": ObjectId(mentor_profile_id)},
            {"$set": {"approved_by_admin": False}},
        )

    async def _notify_admin_mentor_application(self, user_id: str, profile: dict) -> None:
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("email"):
            return
        recipients = await self._get_admin_recipients()
        if not recipients:
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        expertise = ", ".join(profile.get("expertise", []) or [])
        links = ", ".join(profile.get("links", []) or [])
        for recipient in recipients:
            try:
                await self.email_service.send_mentor_application_created(
                    recipient_email=recipient["email"],
                    recipient_name=recipient.get("name", "") or "Admin",
                    applicant_name=user.get("name", "") or "A student",
                    applicant_email=user.get("email", ""),
                    domain=profile.get("domain", ""),
                    experience_years=str(profile.get("experience_years", 0)),
                    expertise=expertise,
                    availability=profile.get("availability", ""),
                    bio=profile.get("bio", ""),
                    links=links,
                    cta_url=f"{base_url}/admin/mentors",
                )
            except Exception:
                continue

    async def _notify_mentor_application_approved(self, mentor_profile_id: str) -> None:
        doc = await self.db.mentor_profiles.find_one({"_id": ObjectId(mentor_profile_id)})
        if not doc:
            return
        profile = normalize_id(doc)
        user = await self.db.users.find_one({"_id": profile["user_id"]})
        if not user or not user.get("email"):
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        try:
            await self.email_service.send_mentor_application_approved(
                recipient_email=user["email"],
                recipient_name=user.get("name", "") or "there",
                cta_url=f"{base_url}/mentor/dashboard",
            )
        except Exception:
            return

    async def _get_admin_recipients(self) -> list[dict]:
        recipients: dict[str, str] = {
            email: "Admin" for email in settings.admin_email_list
        }
        cursor = self.db.users.find({"role": "ADMIN", "blocked": {"$ne": True}})
        async for doc in cursor:
            email = (doc.get("email", "") or "").strip().lower()
            if not email:
                continue
            recipients[email] = doc.get("name", "") or "Admin"
        return [{"email": email, "name": name} for email, name in recipients.items()]
