from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session,joinedload
from fastapi import HTTPException
from typing import List, Optional
from core.database import get_db
from models.officialstat import OfficialStat
from schemas.officialstat import CrimeStatResponse, OfficialStatRead, RegionSchema, CrimeListSchema
from services import official_service

router = APIRouter(tags=["OfficialStatus"])

@router.get("",response_model=CrimeStatResponse)
def get_stats(
    province: str,
    city: str= None,
    major: str = None,
    minor: str = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    data = official_service.fetch_official_stats(db,province,city,major, minor,year)

    if not data:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    return data

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

@router.get("/regions",response_model=list[RegionSchema])
def get_regions(province: str = None, db: Session= Depends(get_db)):
    return official_service.fetch_regions(db,province)

@router.get("/crime-types",response_model=list[CrimeListSchema])
def get_crimes(major:str = None, db:Session = Depends(get_db)):
    return official_service.fetch_crime_types(db,major)