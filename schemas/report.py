from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional

# 모델과 동일하게 소문자로 정의
class ReportStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ReportBase(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportStatusUpdate(BaseModel):
    status: ReportStatus

    @field_validator("status", mode="before")
    @classmethod
    def to_lowercase(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None  # 추가

    model_config = ConfigDict(from_attributes=True)