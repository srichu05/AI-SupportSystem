import logging
from typing import Generator, Optional, Tuple, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings
from backend.app.core.errors import DatabaseNotConfiguredException, DatabaseUnavailableException

logger = logging.getLogger("complaint_assistant.database")

Base = declarative_base()

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_engine() -> Optional[Engine]:
    """Lazily initialize and return the SQLAlchemy engine if configured."""
    global _engine, _SessionFactory
    if _engine is not None:
        return _engine

    if not settings.is_database_configured:
        return None

    db_url = settings.DATABASE_URL
    assert db_url is not None

    try:
        connect_args = {}
        # If SQLite (useful for local fast tests), handle multi-threading
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            _engine = create_engine(db_url, connect_args=connect_args)
        else:
            # PostgreSQL / Supabase
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=300,
            )

        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info("Database engine initialized for: %s", settings.masked_database_url())
        return _engine
    except Exception as e:
        logger.error("Failed to initialize database engine: %s", e)
        return None


def get_session_factory() -> Optional[sessionmaker]:
    """Get the sessionmaker factory."""
    global _SessionFactory
    if _SessionFactory is None:
        get_engine()
    return _SessionFactory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    factory = get_session_factory()
    if factory is None:
        raise DatabaseNotConfiguredException(
            "Database is not configured. Please supply DATABASE_URL in your .env file."
        )

    db: Session = factory()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error("Database session transaction error: %s", e)
        raise
    finally:
        db.close()


def check_database_connectivity() -> Dict[str, Any]:
    """
    Check if the database is configured and reachable.
    Does not throw unhandled exceptions so health checks remain resilient.
    """
    if not settings.is_database_configured:
        return {
            "status": "not_configured",
            "connected": False,
            "message": "DATABASE_URL is not set in environment or .env",
            "masked_url": "not_configured"
        }

    engine = get_engine()
    if engine is None:
        return {
            "status": "error",
            "connected": False,
            "message": "Engine failed to initialize with provided DATABASE_URL",
            "masked_url": settings.masked_database_url()
        }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "connected": True,
            "message": "Database connection verified successfully",
            "masked_url": settings.masked_database_url()
        }
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return {
            "status": "unhealthy",
            "connected": False,
            "message": f"Connection failed: {str(exc).splitlines()[0]}",
            "masked_url": settings.masked_database_url()
        }
