from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum

class ReportCreate(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int
    user_id: int


class RegionSimple(BaseModel):
    id :int
    province: str
    city: Optional[str] = None

class CrimeTypeSimple(BaseModel):
    id: int
    major: str
    minor: str

class ReportRead(BaseModel):
    id: int
    title: str
    content: str
    # ID 대신 혹은 ID와 함께 실제 객체 정보를 담습니다.
    region: RegionSimple
    crime_type: CrimeTypeSimple
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReportUpdate(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportPatch(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    region_id: Optional[int] = None
    crime_type_id: Optional[int] = None


class ReportStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ReportBase(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None  # 추가

    model_config = ConfigDict(from_attributes=True)