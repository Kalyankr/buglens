from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base

# SQLite local database file
SQLALCHEMY_DATABASE_URL = "sqlite:////app/buglens.db"

# connect_args={"check_same_thread": False} is required only for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables if they don't exist."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to provide a DB session to FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
