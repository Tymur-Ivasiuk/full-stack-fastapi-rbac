"""Create one demo user per non-admin role. Idempotent; for local development only.

The admin is created by `initial_data.py` from FIRST_SUPERUSER settings.
"""

import logging

from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.db import engine
from app.core.permissions import Role
from app.models import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEMO_PASSWORD = "changethis"
DEMO_USERS = [
    UserCreate(
        email="manager@example.com",
        password=DEMO_PASSWORD,
        full_name="Demo Manager",
        role=Role.MANAGER,
    ),
    UserCreate(
        email="member@example.com",
        password=DEMO_PASSWORD,
        full_name="Demo Member",
        role=Role.MEMBER,
    ),
]


def main() -> None:
    if settings.FASTAPI_ENV != "development":
        raise SystemExit("Refusing to seed demo users outside FASTAPI_ENV=development")
    with Session(engine) as session:
        for user_in in DEMO_USERS:
            if crud.get_user_by_email(session=session, email=user_in.email):
                logger.info("Demo user %s already exists", user_in.email)
                continue
            crud.create_user(session=session, user_create=user_in)
            logger.info("Created demo %s: %s", user_in.role, user_in.email)


if __name__ == "__main__":
    main()
