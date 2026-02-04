from datetime import datetime
from typing import Optional

from pydantic import BaseModel

#statistics 리스트 안에 들어갈 개별 통계 항목
class CrimeStatDetail(BaseModel):
    crime_major: str # 범죄 대분류
    crime_minor: Optional[str] = None # 범죄 중분류는 없을 수도 있음
    count : int # 발생 건수

    class Config:
        # SQLAlchemy 객체를 pydentic 모델로 자동 변환하기 위해
        from_attributes = True

#최종 API 응답 스키마
class CrimeStatResponse(BaseModel):
    region: str
    year: int
    last_updated: Optional[datetime] = None
    statistics: list[CrimeStatDetail] #위에서 정의한 상세 통계 리스트

    class Config:
        from_attributes = True
