from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from app.utils.errors import AppError
from app.utils.mongo import normalize_id
from app.core.config import settings
from app.services.email_service import EmailService
from app.services.mentor_email_template_service import MentorEmailTemplateService


class RequestService:
    def __init__(self, db):
        self.db = db
        self.email_service = EmailService()
        self.mentor_email_templates = MentorEmailTemplateService(db)

    async def create_request(self, from_user: dict, to_user_id: str, request_type: str, message: str) -> dict:
        if not ObjectId.is_valid(to_user_id):
            raise AppError(400, "invalid_user_id", "Invalid user id")
        if from_user["id"] == to_user_id:
            raise AppError(400, "self_request", "Users cannot message themselves")

        to_user = await self.db.users.find_one({"_id": ObjectId(to_user_id)})
        if not to_user:
            raise AppError(404, "user_not_found", "User not found")

        if request_type == "MENTORSHIP":
            mentor_profile = await self.db.mentor_profiles.find_one(
                {"user_id": ObjectId(to_user_id), "approved_by_admin": True}
            )
            if not mentor_profile:
                raise AppError(400, "mentor_not_available", "Prefect is not available")

        existing = await self.db.requests.find_one(
            {
                "status": "PENDING",
                "$or": [
                    {"from_user_id": ObjectId(from_user["id"]), "to_user_id": ObjectId(to_user_id)},
                    {"from_user_id": ObjectId(to_user_id), "to_user_id": ObjectId(from_user["id"])},
                ],
            }
        )
        if existing:
            raise AppError(409, "request_exists", "An active request already exists")

        now = datetime.now(tz=timezone.utc)
        result = await self.db.requests.insert_one(
            {
                "from_user_id": ObjectId(from_user["id"]),
                "to_user_id": ObjectId(to_user_id),
                "type": request_type,
                "message": message,
                "status": "PENDING",
                "created_at": now,
            }
        )
        doc = await self.db.requests.find_one({"_id": result.inserted_id})
        if request_type == "MENTORSHIP":
            await self._notify_mentor_request_created(from_user, to_user, message)
        else:
            await self._notify_request_created(from_user, to_user, message)
        return self._format_request(normalize_id(doc))

    async def list_incoming(self, user_id: str) -> list[dict]:
        cursor = self.db.requests.find({"to_user_id": ObjectId(user_id)}).sort("created_at", -1)
        return await self._decorate_requests(cursor, user_id, incoming=True)

    async def list_outgoing(self, user_id: str) -> list[dict]:
        cursor = self.db.requests.find({"from_user_id": ObjectId(user_id)}).sort("created_at", -1)
        return await self._decorate_requests(cursor, user_id, incoming=False)

    async def accept_request(self, request_id: str, user_id: str) -> dict:
        request = await self._get_request_for_recipient(request_id, user_id)
        if request["status"] == "ACCEPTED":
            return self._format_request(request)
        if request["status"] != "PENDING":
            raise AppError(400, "invalid_status", "Request is not pending")
        if request.get("type") == "CAPSTONE":
            await self._ensure_team_capacity(request, user_id)
        await self.db.requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "ACCEPTED"}})
        updated = await self.db.requests.find_one({"_id": ObjectId(request_id)})
        if request.get("type") == "MENTORSHIP":
            await self._notify_mentor_request_accepted(request)
        else:
            await self._notify_request_accepted(request)
        return self._format_request(normalize_id(updated))

    async def reject_request(self, request_id: str, user_id: str) -> dict:
        request = await self._get_request_for_recipient(request_id, user_id)
        if request["status"] == "REJECTED":
            return self._format_request(request)
        if request["status"] != "PENDING":
            raise AppError(400, "invalid_status", "Request is not pending")
        await self.db.requests.update_one({"_id": ObjectId(request_id)}, {"$set": {"status": "REJECTED"}})
        updated = await self.db.requests.find_one({"_id": ObjectId(request_id)})
        return self._format_request(normalize_id(updated))

    async def _get_request_for_recipient(self, request_id: str, user_id: str) -> dict:
        if not ObjectId.is_valid(request_id):
            raise AppError(400, "invalid_request_id", "Invalid request id")
        request = await self.db.requests.find_one({"_id": ObjectId(request_id), "to_user_id": ObjectId(user_id)})
        if not request:
            raise AppError(404, "request_not_found", "Request not found")
        return normalize_id(request)

    async def _decorate_requests(self, cursor, user_id: str, incoming: bool) -> list[dict]:
        results = []
        async for doc in cursor:
            req = normalize_id(doc)
            counterpart_id = req["from_user_id"] if incoming else req["to_user_id"]
            user = await self.db.users.find_one({"_id": counterpart_id})
            if not user:
                continue
            email = user["email"] if req["status"] == "ACCEPTED" else None
            results.append(
                {
                    "id": req["id"],
                    "from_user_id": str(req["from_user_id"]),
                    "to_user_id": str(req["to_user_id"]),
                    "type": req.get("type"),
                    "message": req.get("message", ""),
                    "status": req.get("status"),
                    "created_at": req.get("created_at"),
                    "counterpart_name": user.get("name", ""),
                    "counterpart_role": user.get("role", "USER"),
                    "counterpart_email": email,
                }
            )
        return results

    def _format_request(self, request: dict) -> dict:
        return {
            "id": request["id"],
            "from_user_id": str(request["from_user_id"]),
            "to_user_id": str(request["to_user_id"]),
            "type": request.get("type"),
            "message": request.get("message", ""),
            "status": request.get("status"),
            "created_at": request.get("created_at"),
        }

    async def _notify_request_created(self, from_user: dict, to_user: dict, message: str) -> None:
        if not to_user.get("email"):
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        try:
            await self.email_service.send_request_created(
                recipient_email=to_user["email"],
                recipient_name=to_user.get("name", ""),
                sender_name=from_user.get("name", ""),
                message=message or "",
                cta_url=f"{base_url}/requests",
                profile_url=f"{base_url}/profile?user_id={from_user['id']}",
            )
        except Exception:
            return

    async def _notify_request_accepted(self, request: dict) -> None:
        from_id = request["from_user_id"]
        to_id = request["to_user_id"]
        if not isinstance(from_id, ObjectId):
            from_id = ObjectId(from_id)
        if not isinstance(to_id, ObjectId):
            to_id = ObjectId(to_id)
        from_user = await self.db.users.find_one({"_id": from_id})
        to_user = await self.db.users.find_one({"_id": to_id})
        if not from_user or not from_user.get("email"):
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        try:
            await self.email_service.send_request_accepted(
                recipient_email=from_user["email"],
                recipient_name=from_user.get("name", ""),
                accepter_name=(to_user or {}).get("name", ""),
                cta_url=f"{base_url}/requests",
            )
        except Exception:
            return

    async def _notify_mentor_request_created(self, from_user: dict, to_user: dict, message: str) -> None:
        if not to_user.get("email"):
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        try:
            mentor_id = str(to_user.get("id") or to_user.get("_id"))
            html_body = await self.mentor_email_templates.render_with_context(
                mentor_id,
                "mentor_request_created",
                {
                    "recipient_name": to_user.get("name", "") or "Prefect",
                    "sender_name": from_user.get("name", "") or "A NYA student",
                    "message": message or "",
                    "cta_url": f"{base_url}/mentor/dashboard",
                },
            )
            subject = f"{from_user.get('name', 'A student')} requested mentorship"
            await self.email_service.send_custom_html(to_user["email"], subject, html_body)
        except Exception:
            return

    async def _notify_mentor_request_accepted(self, request: dict) -> None:
        from_id = request["from_user_id"]
        to_id = request["to_user_id"]
        if not isinstance(from_id, ObjectId):
            from_id = ObjectId(from_id)
        if not isinstance(to_id, ObjectId):
            to_id = ObjectId(to_id)
        student = await self.db.users.find_one({"_id": from_id})
        mentor = await self.db.users.find_one({"_id": to_id})
        if not student or not student.get("email"):
            return
        base_url = settings.frontend_origin or "http://localhost:8000"
        try:
            html_body = await self.mentor_email_templates.render_with_context(
                str(to_id),
                "mentor_request_accepted",
                {
                    "recipient_name": student.get("name", "") or "there",
                    "mentor_name": (mentor or {}).get("name", "") or "A NYA mentor",
                    "cta_url": f"{base_url}/requests",
                },
            )
            subject = f"{(mentor or {}).get('name', 'A mentor')} accepted your mentorship request"
            await self.email_service.send_custom_html(student["email"], subject, html_body)
        except Exception:
            return

    async def _ensure_team_capacity(self, request: dict, user_id: str) -> None:
        to_id = request["to_user_id"]
        from_id = request["from_user_id"]
        if not isinstance(to_id, ObjectId):
            to_id = ObjectId(to_id)
        if not isinstance(from_id, ObjectId):
            from_id = ObjectId(from_id)
        recipient_id = ObjectId(user_id)

        team_limit = 5
        base_query = {
            "status": "ACCEPTED",
            "type": "CAPSTONE",
            "$or": [
                {"from_user_id": recipient_id},
                {"to_user_id": recipient_id},
            ],
        }
        recipient_count = await self.db.requests.count_documents(base_query)
        if recipient_count >= team_limit:
            raise AppError(400, "team_full", "Your team already has 5 members")

        other_query = {
            "status": "ACCEPTED",
            "type": "CAPSTONE",
            "$or": [
                {"from_user_id": from_id},
                {"to_user_id": from_id},
            ],
        }
        other_count = await self.db.requests.count_documents(other_query)
        if other_count >= team_limit:
            raise AppError(400, "team_full", "This member already has a full team")
