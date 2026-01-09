import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BugJob(Base):
    __tablename__ = "bug_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    vision_file_path = Column(String, nullable=True)
    summary = Column(JSON, nullable=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
