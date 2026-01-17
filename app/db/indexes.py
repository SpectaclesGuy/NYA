from __future__ import annotations

from pymongo import ASCENDING, IndexModel


async def create_indexes(db) -> None:
    await db.users.create_indexes(
        [
            IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
            IndexModel([("role", ASCENDING)], name="role_idx"),
        ]
    )

    await db.capstone_profiles.create_indexes(
        [
            IndexModel([("user_id", ASCENDING)], unique=True, name="uniq_user_id"),
            IndexModel([("skills", ASCENDING)], name="skills_idx"),
            IndexModel([("required_skills", ASCENDING)], name="required_skills_idx"),
            IndexModel([("looking_for", ASCENDING)], name="looking_for_idx"),
            IndexModel([("mentor_assigned", ASCENDING)], name="mentor_assigned_idx"),
        ]
    )

    await db.mentor_profiles.create_indexes(
        [
            IndexModel([("user_id", ASCENDING)], unique=True, name="uniq_user_id"),
            IndexModel([("approved_by_admin", ASCENDING)], name="approved_idx"),
            IndexModel([("domain", ASCENDING)], name="domain_idx"),
        ]
    )

    await db.requests.create_indexes(
        [
            IndexModel([("from_user_id", ASCENDING), ("to_user_id", ASCENDING), ("status", ASCENDING)], name="request_pair_status_idx"),
            IndexModel([("to_user_id", ASCENDING), ("status", ASCENDING)], name="incoming_status_idx"),
            IndexModel([("from_user_id", ASCENDING), ("status", ASCENDING)], name="outgoing_status_idx"),
            IndexModel([("type", ASCENDING)], name="type_idx"),
        ]
    )
