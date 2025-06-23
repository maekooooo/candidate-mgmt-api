import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime, Boolean, JSON, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class Candidate(Base):
    """
    Candidate model for the recruitment system.
    """
    __tablename__ = "candidates"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name       = Column(String(255), nullable=False)
    email           = Column(String(255), nullable=False, unique=True)
    phone           = Column(String(20), nullable=True)
    skills          = Column(JSONB, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications    = relationship(
        "Application",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )