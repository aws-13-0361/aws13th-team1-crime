from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from core.database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    province = Column(String(50), nullable=False, index=True)
    city = Column(String(50), nullable=True)
    full_name = Column(String(100), unique=True, nullable=False, index=True)

    official_stat = relationship("OfficialStat",back_populates="region")
    reports = relationship("Report", back_populates="region")