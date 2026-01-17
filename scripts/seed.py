from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import settings


SEED_TARGET = 100
RANDOM_SEED = 42

BASE_USERS = [
    {"name": "Mayank Tyagi", "email": "mtyagi_be22@thapar.edu", "role": "ADMIN"},
    {"name": "Aarav Singh", "email": "aarav@thapar.edu", "role": "USER"},
    {"name": "Riya Sharma", "email": "riya@thapar.edu", "role": "USER"},
    {"name": "Ishaan Verma", "email": "ishaan@thapar.edu", "role": "USER"},
    {"name": "Dr. Meera Nair", "email": "meera@thapar.edu", "role": "MENTOR"},
    {"name": "Prof. Karan Malik", "email": "karan@thapar.edu", "role": "MENTOR"},
    {"name": "Mayank Admin", "email": "mtyagi2002@gmail.com", "role": "ADMIN"},
]

BASE_CAPSTONE_PROFILES = {
    "mtyagi_be22@thapar.edu": {
        "skills": ["Python", "FastAPI", "MongoDB", "UX"],
        "required_skills": ["React", "UI/UX", "Design"],
        "links": ["https://github.com", "https://linkedin.com"],
        "looking_for": "TEAM",
        "mentor_assigned": False,
        "bio": "Building a capstone platform for better team discovery.",
        "availability": "Evenings, 6-8 hrs/week",
    },
    "aarav@thapar.edu": {
        "skills": ["React", "UI/UX", "Prototyping"],
        "required_skills": ["Backend", "APIs", "Data"],
        "links": ["https://portfolio.com"],
        "looking_for": "MEMBER",
        "mentor_assigned": False,
        "bio": "Interested in product design and accessibility.",
        "availability": "Weekends",
    },
    "riya@thapar.edu": {
        "skills": ["Data Science", "NLP", "Python"],
        "required_skills": ["IoT", "Sensors"],
        "links": ["https://linkedin.com"],
        "looking_for": "TEAM",
        "mentor_assigned": True,
        "bio": "Working on a smart campus assistant.",
        "availability": "Mornings",
    },
    "ishaan@thapar.edu": {
        "skills": ["IoT", "Embedded", "C++", "Sensors"],
        "required_skills": ["ML", "Dashboard"],
        "links": ["https://github.com"],
        "looking_for": "MEMBER",
        "mentor_assigned": False,
        "bio": "Building low-power sensing networks.",
        "availability": "Late nights",
    },
}

BASE_MENTOR_PROFILES = {
    "meera@thapar.edu": {
        "domain": "AI",
        "experience_years": 12,
        "expertise": ["NLP", "Ethics", "ML Systems"],
        "links": ["https://linkedin.com", "https://scholar.google.com"],
        "bio": "Guiding teams building responsible AI projects.",
        "availability": "Tue/Thu afternoons",
        "approved_by_admin": True,
    },
    "karan@thapar.edu": {
        "domain": "Fintech",
        "experience_years": 15,
        "expertise": ["Payments", "Risk", "Security"],
        "links": ["https://linkedin.com"],
        "bio": "Mentoring capstone teams in fintech and security.",
        "availability": "Weekends",
        "approved_by_admin": True,
    },
}

FIRST_NAMES = [
    "Aanya", "Arjun", "Diya", "Kabir", "Ira", "Neel", "Sara", "Vihaan",
    "Anaya", "Reyansh", "Kiara", "Advait", "Myra", "Rohan", "Tara", "Vivaan",
    "Ishika", "Ritvik", "Mehul", "Anika", "Samar", "Kritika", "Harsh", "Naina",
]
LAST_NAMES = [
    "Sharma", "Singh", "Verma", "Gupta", "Kapoor", "Malik", "Agarwal", "Mehta",
    "Bhatia", "Saxena", "Nair", "Reddy", "Joshi", "Iyer", "Chopra", "Kohli",
    "Bansal", "Arora", "Sethi", "Khanna", "Das", "Kumar", "Patel", "Mishra",
]
SKILLS = [
    "Python", "FastAPI", "MongoDB", "React", "Node.js", "UI/UX", "Figma", "C++",
    "IoT", "NLP", "Data Science", "ML", "DevOps", "Kubernetes", "Flutter", "Django",
    "Typescript", "Analytics", "Security", "Product", "Design", "Research",
]
DOMAINS = ["AI", "Fintech", "HealthTech", "EdTech", "IoT", "Security", "Design", "Robotics"]
AVAILABILITY = ["Evenings", "Weekends", "Mornings", "Afternoons", "Flexible"]


def build_seed_data() -> tuple[list[dict], dict, dict]:
    import random

    random.seed(RANDOM_SEED)
    users = list(BASE_USERS)
    capstone_profiles = dict(BASE_CAPSTONE_PROFILES)
    mentor_profiles = dict(BASE_MENTOR_PROFILES)

    existing_emails = {user["email"] for user in users}
    target = SEED_TARGET

    index = 1
    while len(users) < target:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}{index}@thapar.edu"
        index += 1
        if email in existing_emails:
            continue
        existing_emails.add(email)

        is_mentor = random.random() < 0.12
        role = "MENTOR" if is_mentor else "USER"
        users.append({"name": f"{first} {last}", "email": email, "role": role})

        if is_mentor:
            mentor_profiles[email] = {
                "domain": random.choice(DOMAINS),
                "experience_years": random.randint(3, 18),
                "expertise": random.sample(SKILLS, k=3),
                "links": ["https://linkedin.com", "https://scholar.google.com"],
                "bio": "Mentoring capstone teams across multiple disciplines.",
                "availability": random.choice(AVAILABILITY),
                "approved_by_admin": random.random() < 0.7,
            }
        else:
            skills = random.sample(SKILLS, k=4)
            capstone_profiles[email] = {
                "skills": skills,
                "required_skills": random.sample([s for s in SKILLS if s not in skills], k=3),
                "links": ["https://github.com", "https://linkedin.com"],
                "looking_for": random.choice(["TEAM", "MEMBER"]),
                "mentor_assigned": random.random() < 0.35,
                "bio": "Exploring a capstone idea with a strong product focus.",
                "availability": random.choice(AVAILABILITY),
            }

    return users, capstone_profiles, mentor_profiles


async def upsert_user(db, user: dict) -> ObjectId:
    now = datetime.now(tz=timezone.utc)
    await db.users.update_one(
        {"email": user["email"]},
        {
            "$set": {"name": user["name"], "role": user["role"], "last_login": now, "role_selected": True},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    doc = await db.users.find_one({"email": user["email"]})
    return doc["_id"]


async def upsert_capstone(db, user_id: ObjectId, profile: dict) -> None:
    await db.capstone_profiles.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, **profile}},
        upsert=True,
    )


async def upsert_mentor(db, user_id: ObjectId, profile: dict) -> None:
    await db.mentor_profiles.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, **profile}},
        upsert=True,
    )


async def seed_requests(db, user_ids: dict[str, ObjectId]) -> None:
    pairs = [
        ("mtyagi_be22@thapar.edu", "aarav@thapar.edu", "CAPSTONE", "Looking to form a team focused on UX + backend."),
        ("riya@thapar.edu", "ishaan@thapar.edu", "CAPSTONE", "Need hardware support for our campus assistant."),
        ("mtyagi_be22@thapar.edu", "meera@thapar.edu", "MENTORSHIP", "Requesting mentorship for backend architecture."),
    ]
    now = datetime.now(tz=timezone.utc)
    for from_email, to_email, req_type, message in pairs:
        existing = await db.requests.find_one(
            {
                "from_user_id": user_ids[from_email],
                "to_user_id": user_ids[to_email],
                "status": "PENDING",
            }
        )
        if existing:
            continue
        await db.requests.insert_one(
            {
                "from_user_id": user_ids[from_email],
                "to_user_id": user_ids[to_email],
                "type": req_type,
                "message": message,
                "status": "PENDING",
                "created_at": now,
            }
        )


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    users, capstone_profiles, mentor_profiles = build_seed_data()
    user_ids: dict[str, ObjectId] = {}
    for user in users:
        user_id = await upsert_user(db, user)
        user_ids[user["email"]] = user_id

    for email, profile in capstone_profiles.items():
        if email in user_ids:
            await upsert_capstone(db, user_ids[email], profile)

    for email, profile in mentor_profiles.items():
        if email in user_ids:
            await upsert_mentor(db, user_ids[email], profile)

    await seed_requests(db, user_ids)
    client.close()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
