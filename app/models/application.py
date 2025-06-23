import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApplicationStatus(enum.Enum):
    APPLIED         = "APPLIED"
    INTERVIEWING    = "INTERVIEWING"
    REJECTED        = "REJECTED"
    HIRED           = "HIRED"

class Application(Base):
    """
    Application model for the recruitment system.
    """
    __tablename__ = "applications"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id    = Column(UUID(as_uuid=True), ForeignKey('candidates.id'), nullable=False)
    job_title       = Column(String(255), nullable=False)
    status          = Column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        server_default=ApplicationStatus.APPLIED.value,
    )
    applied_at      = Column(DateTime, default=datetime.utcnow)

    candidate       = relationship("Candidate", back_populates="applications")
