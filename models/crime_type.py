from sqlalchemy import Column, Integer, String, UniqueConstraint
from core.database import Base

class CrimeType(Base):
    __tablename__ = "crime_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    major = Column(String(50), nullable=False, index=True)
    minor = Column(String(50), nullable=True)

    # major와 minor의 조합이 유니크해야 함 (SQL 스키마 반영)
    __table_args__ = (UniqueConstraint('major', 'minor', name='unique_crime_type'),)