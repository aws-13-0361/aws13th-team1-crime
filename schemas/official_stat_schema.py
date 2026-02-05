from pydantic import BaseModel
from schemas.report_schema import RegionSimple, CrimeTypeSimple


class OfficialStatBase(BaseModel):
    region_id: int
    crime_type_id: int
    count: int
    year: int

class OfficialStatCreate(OfficialStatBase):
    pass

class OfficialStatRead(OfficialStatBase):
    id: int
    # ID 대신(또는 함께) 실제 객체 정보를 담도록 설정
    region: RegionSimple
    crime_type: CrimeTypeSimple

    class Config:
        from_attributes = True