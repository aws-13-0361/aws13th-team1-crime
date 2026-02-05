from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from services import report_service  # 아까 만든 서비스 파일
from schemas.report import ReportResponse  # 아까 만든 스키마
from typing import List, Optional
from models.report import ReportStatus

router = APIRouter(tags=["Admin"])


# 승인 API 엔드포인트
@router.post("/reports/{report_id}/approve", response_model=ReportResponse)
def approve_report(report_id: int, db: Session = Depends(get_db)):
    try:
        updated_report = report_service.update_report_status(
            db=db,
            report_id=report_id,
            new_status=ReportStatus.approved
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")

    return updated_report

@router.post("/reports/{report_id}/reject", response_model=ReportResponse)
def reject_report(report_id: int, db: Session = Depends(get_db)):
    try:
        updated_report = report_service.update_report_status(db, report_id, ReportStatus.rejected)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")
    return updated_report

@router.get("/reports", response_model=List[ReportResponse])
def get_reports(
    status: Optional[ReportStatus] = None,
    skip: int = Query(0, ge=0),              # 0보다 크거나 같아야 함
    limit: int = Query(100, ge=1, le=500),   # 1~500 사이만 허용!
    db: Session = Depends(get_db)
):
    reports = report_service.get_all_reports(db, skip=skip, limit=limit, status=status)
    return reports
