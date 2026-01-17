from __future__ import annotations

import re

from bson import ObjectId

from app.utils.mongo import normalize_id


class DiscoveryService:
    def __init__(self, db):
        self.db = db

    async def discover_users(
        self,
        current_user_id: str,
        skills: list[str] | None = None,
        search: str | None = None,
        looking_for: str | None = None,
        mentor_assigned: bool | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> list[dict]:
        base_query: dict = {}
        if looking_for:
            base_query["looking_for"] = looking_for
        if mentor_assigned is not None:
            base_query["mentor_assigned"] = mentor_assigned

        skills_terms = skills or []
        name_query = None
        if search and search.strip():
            name_query = search.strip()
            extra_terms = [part for part in re.split(r"[,\s]+", name_query) if part]
            skills_terms = list({*skills_terms, *extra_terms})

        profiles_by_user: dict[str, dict] = {}
        fetch_multiplier = max(3, page + 2)
        fetch_limit = limit * fetch_multiplier

        if not skills_terms and not name_query:
            query = {**base_query, "user_id": {"$ne": ObjectId(current_user_id)}}
            cursor = self.db.capstone_profiles.find(query).sort("user_id", 1).limit(fetch_limit)
            async for doc in cursor:
                profile = normalize_id(doc)
                profiles_by_user[str(profile["user_id"])] = profile
        else:
            if name_query:
                regex = re.compile(re.escape(name_query), re.IGNORECASE)
                user_cursor = self.db.users.find({"name": regex}, {"_id": 1})
                user_ids = [user["_id"] async for user in user_cursor]
                if user_ids:
                    query = {**base_query, "user_id": {"$in": user_ids, "$ne": ObjectId(current_user_id)}}
                    cursor = self.db.capstone_profiles.find(query).limit(fetch_limit)
                    async for doc in cursor:
                        profile = normalize_id(doc)
                        profiles_by_user[str(profile["user_id"])] = profile
            if skills_terms:
                patterns = [re.compile(f"^{re.escape(skill)}$", re.IGNORECASE) for skill in skills_terms]
                query = {**base_query, "skills": {"$in": patterns}, "user_id": {"$ne": ObjectId(current_user_id)}}
                cursor = self.db.capstone_profiles.find(query).limit(fetch_limit)
                async for doc in cursor:
                    profile = normalize_id(doc)
                    profiles_by_user[str(profile["user_id"])] = profile

        profiles = list(profiles_by_user.values())
        ranked = self._rank_by_skill_match(profiles, skills_terms)
        results = []
        start = (page - 1) * limit
        for profile in ranked[start:start + limit]:
            user = await self.db.users.find_one({"_id": profile["user_id"]})
            if not user:
                continue
            if user.get("role") == "ADMIN":
                continue
            team_count, team_status = await self._get_team_status(profile["user_id"])
            results.append(
                {
                    "id": str(profile["user_id"]),
                    "name": user["name"],
                    "skills": profile.get("skills", []),
                    "looking_for": profile.get("looking_for"),
                    "team_status": team_status,
                    "team_count": team_count,
                }
            )
        return results

    async def recommended_users(self, current_user_id: str, limit: int = 10) -> list[dict]:
        profile = await self.db.capstone_profiles.find_one({"user_id": ObjectId(current_user_id)})
        required = profile.get("required_skills", []) if profile else []
        if required:
            patterns = [re.compile(f"^{re.escape(skill)}$", re.IGNORECASE) for skill in required]
            cursor = self.db.capstone_profiles.find({"skills": {"$in": patterns}}).limit(limit * 3)
            candidates = []
            async for doc in cursor:
                profile_doc = normalize_id(doc)
                if str(profile_doc["user_id"]) == current_user_id:
                    continue
                candidates.append(profile_doc)
            ranked = self._rank_by_skill_match(candidates, required)
            picks = ranked[:limit]
        else:
            pipeline = [{"$match": {"user_id": {"$ne": ObjectId(current_user_id)}}}, {"$sample": {"size": limit}}]
            cursor = self.db.capstone_profiles.aggregate(pipeline)
            picks = [normalize_id(doc) async for doc in cursor]

        results = []
        for profile in picks:
            user = await self.db.users.find_one({"_id": profile["user_id"]})
            if not user:
                continue
            if user.get("role") == "ADMIN":
                continue
            team_count, team_status = await self._get_team_status(profile["user_id"])
            results.append(
                {
                    "id": str(profile["user_id"]),
                    "name": user["name"],
                    "skills": profile.get("skills", []),
                    "looking_for": profile.get("looking_for"),
                    "team_status": team_status,
                    "team_count": team_count,
                }
            )
        return results

    def _rank_by_skill_match(self, profiles: list[dict], skills: list[str]) -> list[dict]:
        if not skills:
            return sorted(profiles, key=lambda p: str(p.get("user_id")))

        norm_skills = {skill.strip().lower() for skill in skills if skill.strip()}

        def score(profile: dict) -> int:
            profile_skills = {s.lower() for s in profile.get("skills", [])}
            return len(profile_skills & norm_skills)

        return sorted(profiles, key=lambda p: (-score(p), str(p.get("user_id"))))

    async def _get_team_status(self, user_id: ObjectId) -> tuple[int, str]:
        query = {
            "status": "ACCEPTED",
            "type": "CAPSTONE",
            "$or": [
                {"from_user_id": user_id},
                {"to_user_id": user_id},
            ],
        }
        count = await self.db.requests.count_documents(query)
        if count == 0:
            return count, "AVAILABLE"
        if count >= 5:
            return count, "BOOKED"
        return count, "IN_TEAM"
