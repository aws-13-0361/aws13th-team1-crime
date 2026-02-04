import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status,Depends
from sqlalchemy.orm import Session
from schemas.report_schema import ReportRead, ReportCreate
from utils.database import get_db
from models import User, Region, CrimeType, Report


router = APIRouter(prefix="/api", tags=["Reports"])

# 1. 제보 목록 (필터링/페이징)
@router.get("/reports", response_model=List[ReportRead])
async def get_report(
     db: Session = Depends(get_db)):
    try:
        reports = db.query(Report).all()
        return reports

    except HTTPException:
        raise
    except Exception as e:
       print(f"Service Error: {e}")
       raise HTTPException(status_code=500, detail="Internal Server Error")



# 2. 제보 상세
@router.get("/{report_id}", response_model=ReportRead)
async def get_report(report_id: int):
    # TODO: DB에서 ID로 단일 건 조회
    # if not report: raise HTTPException(status_code=404)
    return {"id": report_id, "title": "샘플", "content": "내용"}

# 3. 제보 작성
@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReportRead)
async def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db)
):
    # TODO: DB 저장 로직







    return {**report.model_dump(), "id": 1, "created_at": datetime.now()}

# 4. 제보 수정
@router.put("/{report_id}", response_model=ReportRead)
async def update_report(report_id: int, report_update: ReportCreate):
    # TODO: 해당 ID 존재 확인 및 수정 로직
    return {**report_update.model_dump(), "id": report_id, "created_at": datetime.now()}

# 5. 제보 삭제
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: int):
    # TODO: DB 삭제 로직
    return None