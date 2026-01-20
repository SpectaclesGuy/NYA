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


SEED_TARGET = 1
RANDOM_SEED = 42

BASE_USERS = [
    {"name": "Mayank Tyagi", "email": "mtyagi_be22@thapar.edu", "role": "MENTOR"},
]

BASE_CAPSTONE_PROFILES = {}

BASE_MENTOR_PROFILES = {
    "mtyagi_be22@thapar.edu": {
        "domain": "Python, FastAPI, MongoDB, UX, n8n, GenAI, Diffusion, C/C++",
        "experience_years": 1,
        "expertise": ["Python", "FastAPI", "MongoDB", "UX", "n8n", "GenAI", "Diffusion", "C/C++"],
        "links": [
            "https://www.linkedin.com/in/mayank-tyagi-599703326/",
            "https://github.com/SpectaclesGuy",
        ],
        "bio": "Not waiting for my Hogwarts letter.",
        "availability": "I have no idea",
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
    return


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
