from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from models.report import ReportStatus

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