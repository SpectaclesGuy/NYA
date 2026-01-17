from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import settings


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]
    admin_ids = [user["_id"] async for user in db.users.find({"role": "ADMIN"}, {"_id": 1})]
    await db.users.delete_many({"role": {"$ne": "ADMIN"}})
    if admin_ids:
      await db.capstone_profiles.delete_many({"user_id": {"$nin": admin_ids}})
      await db.mentor_profiles.delete_many({"user_id": {"$nin": admin_ids}})
    else:
      await db.capstone_profiles.delete_many({})
      await db.mentor_profiles.delete_many({})
    await db.requests.delete_many({})
    client.close()
    print("Database cleared.")


if __name__ == "__main__":
    asyncio.run(main())
