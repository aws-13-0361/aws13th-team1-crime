from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportBase(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportCreate(ReportBase):
    user_id: int # 현재 로그인한 유저 ID를 할당

class ReportRead(ReportBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True # SQLAlchemy 객체를 자동으로 dict로 변환