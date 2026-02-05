from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship

from core.database import Base

class OfficialStat(Base):
    __tablename__ = "official_stats"
    id = Column(Integer, primary_key=True,autoincrement=True)
    region_id = Column(Integer,ForeignKey("regions.id"),nullable=False)
    crime_type_id = Column(Integer,ForeignKey("crime_types.id"),nullable=True)
    year = Column(Integer,nullable=False,index=True)
    count = Column(Integer,server_default="0",nullable=False)
    last_updated = Column(TIMESTAMP,server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    region = relationship("Region",back_populates="official_stat")
    crime_type = relationship("CrimeType")