from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.app.core.database import get_db


def get_database_session() -> Generator[Session, None, None]:
    """Dependency that yields an active database session."""
    yield from get_db()
