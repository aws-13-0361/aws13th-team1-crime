from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models.official_stat_model import OfficialStat
from schemas.official_stat_schema import OfficialStatRead
from utils.database import get_db

router = APIRouter(prefix="/api/official-stats", tags=["OfficialStats"])
# app/api/endpoints/official_stats_endpoint.py

from sqlalchemy.orm import joinedload  # 이 부분이 중요합니다!


@router.get("/", response_model=List[OfficialStatRead])
def get_official_stats(
        region_id: Optional[int] = None,
        crime_type_id: Optional[int] = None,
        year: Optional[int] = None,
        db: Session = Depends(get_db)
):
    query = db.query(OfficialStat).options(
        joinedload(OfficialStat.region),  # Region 테이블 Join
        joinedload(OfficialStat.crime_type)  # CrimeType 테이블 Join
    )

    if region_id:
        query = query.filter(OfficialStat.region_id == region_id)
    if crime_type_id:
        query = query.filter(OfficialStat.crime_type_id == crime_type_id)
    if year:
        query = query.filter(OfficialStat.year == year)

    return query.order_by(OfficialStat.year.asc()).all()