import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BugJob(Base):
    __tablename__ = "bug_jobs"

    # Using UUIDs for Job IDs is more secure than simple integers
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    # Store a summary of the video report
    summary = Column(JSON, nullable=True)

    # Statuses: PENDING, PROCESSING, COMPLETED, FAILED
    status = Column(String, default="PENDING")

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    # Store the final fused JSON report here
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
