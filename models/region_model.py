from sqlalchemy import Column, Integer, String
from core.db_connection import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    province = Column(String(50))  # 시/도
    city = Column(String(50))      # 시/군/구
    full_name = Column(String(100), unique=True) # 전체 지역명