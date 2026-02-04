
from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

import schemas.officialstat
from core.database import get_db
from services import official_service

router = APIRouter(prefix="/api/stats")

@router.get("",response_model=schemas.officialstat.CrimeStatDetail)
def get_stats(province:str, city:str, year:int = None, db:Session = Depends(get_db())):
    data = official_service.fetch_official_stats(db,province,city,year)

    if not data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    return data