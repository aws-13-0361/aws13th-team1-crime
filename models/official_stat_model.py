from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.db_connection import Base

class OfficialStat(Base):
    __tablename__ = "official_stats"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    crime_type_id = Column(Integer, ForeignKey("crime_types.id"), nullable=False)
    count = Column(Integer, default=0) # 발생 건수
    year = Column(Integer, nullable=False)        # 통계 연도
    # 관계 설정 (필요 시)
    region = relationship("Region")
    crime_type = relationship("CrimeType")