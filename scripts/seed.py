import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.repositories.organizations import get_or_create as get_or_create_organization
from app.repositories.users import get_or_create as get_or_create_user

SEED_PASSWORD = "password123"
SEED_ORGANIZATIONS = [
    {
        "slug": "demo",
        "name": "Demo Organization",
        "users": [
            ("admin@example.com", "admin"),
            ("analyst@example.com", "analyst"),
            ("viewer@example.com", "viewer"),
        ],
    },
    {
        "slug": "other",
        "name": "Other Organization",
        "users": [("other-admin@example.com", "admin")],
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        password_hash = hash_password(SEED_PASSWORD)
        for organization_data in SEED_ORGANIZATIONS:
            organization = await get_or_create_organization(
                session,
                slug=organization_data["slug"],
                name=organization_data["name"],
            )
            for email, role in organization_data["users"]:
                await get_or_create_user(
                    session,
                    organization_id=organization.id,
                    email=email,
                    password_hash=password_hash,
                    role=role,
                )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
