from __future__ import annotations


def is_capstone_profile_complete(doc: dict | None) -> bool:
    if not doc:
        return False
    skills = [skill for skill in doc.get("skills", []) if str(skill).strip()]
    required_skills = [skill for skill in doc.get("required_skills", []) if str(skill).strip()]
    links = [link for link in doc.get("links", []) if str(link).strip()]
    bio = str(doc.get("bio") or "").strip()
    availability = str(doc.get("availability") or "").strip()
    looking_for = doc.get("looking_for")
    return bool(
        skills
        and required_skills
        and links
        and bio
        and availability
        and looking_for in {"TEAM", "MEMBER"}
    )
