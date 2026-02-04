from http.cookiejar import offset_from_tz_string

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException

import schemas.officialstat
from core.database import get_db
from services import official_service

router = APIRouter()

@router.get("",response_model=schemas.officialstat.CrimeStatResponse)
def get_stats(
    province: str,
    city: str,
    major: str = None,
    minor: str = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    data = official_service.fetch_official_stats(db,province,city,major, minor,year)

    if not data:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    return data

@router.get("/regions",response_model=list[schemas.officialstat.RegionSchema])
def get_regions(province: str = None, db: Session= Depends(get_db)):
    return official_service.fetch_regions(db,province)

@router.get("/crime-types",response_model=list[schemas.officialstat.CrimeListSchema])
def get_crimes(major:str = None, db:Session = Depends(get_db)):
    return official_service.fetch_crime_types(db,major)