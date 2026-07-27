from sqlalchemy import JSON, Column, DateTime, String, func

from noray.database import Base


class ProfileModel(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    data = Column(JSON, nullable=False)  # Stores the full CareerProfile structure
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
