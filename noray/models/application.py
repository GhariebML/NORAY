from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, func

from noray.database import Base


class ApplicationModel(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # 'job' or 'scholarship'
    title = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # 'discovered', 'submitted', etc.
    applied_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    priority = Column(String(20), default="medium")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
