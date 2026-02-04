from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from services import report_service  # 아까 만든 서비스 파일
from schemas.report import ReportResponse, ReportStatus  # 아까 만든 스키마

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# 승인 API 엔드포인트
@router.post("/reports/{report_id}/approve", response_model=ReportResponse)
def approve_report(report_id: int, db: Session = Depends(get_db)):
    # 1. 서비스 함수를 호출해서 상태를 'approved'로 변경 시도
    updated_report = report_service.update_report_status(
        db=db,
        report_id=report_id,
        new_status=ReportStatus.approved
    )

    # 2. 만약 해당 ID의 제보가 없어서 결과가 None이면 404 에러를 던짐
    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")

    # 3. 성공하면 업데이트된 제보 정보를 반환 (스키마 형식에 맞춰서!)
    return updated_report