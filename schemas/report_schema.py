from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportBase(BaseModel):
    title: str
    content: str
    region_id: int
    crime_type_id: int

class ReportCreate(BaseModel):
    title: str
    content: str
    region_id: int        # 프론트에서 선택한 지역의 ID
    crime_type_id: int    # 프론트에서 선택한 범죄 유형의 ID
    # user_id는 보통 로그인 세션/토큰에서 가져오므로 입력 모델에서는 제외하거나 선택적으로 둡니다.
    user_id: int
class RegionSimple(BaseModel):
    province: str
    city: str

class CrimeTypeSimple(BaseModel):
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