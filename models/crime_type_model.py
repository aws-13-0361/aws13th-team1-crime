from sqlalchemy import Column, Integer, String
from core.db_connection import Base

class CrimeType(Base):
    __tablename__ = "crime_types"

    id = Column(Integer, primary_key=True, index=True)
    major = Column(String(50))  # 범죄 대분류
    minor = Column(String(50))  # 범죄 중분류