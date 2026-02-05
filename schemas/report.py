from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum  # 1. Enum 사용을 위해 임포트

# 2. 모델에서 정의한 ReportStatus를 가져와서 '단일 출처' 원칙을 지킵니다.
from models.report import ReportStatus

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

# --- 3. 중복 정의된 ReportStatus 클래스는 삭제했습니다 (import로 대체) ---

class ReportBase(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus  # 이제 위에서 import한 모델의 Enum을 사용합니다.
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)