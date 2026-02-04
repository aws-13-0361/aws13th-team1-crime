
from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException

import schemas.officialstat
from core.database import get_db
from services import official_service

router = APIRouter()

# CrimeStatDetail이 아닌 CrimeStatResponse
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