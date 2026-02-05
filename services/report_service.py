from sqlalchemy.orm import Session
from models.report import Report, ReportStatus
from datetime import datetime, timezone
from typing import Optional

def update_report_status(db: Session, report_id: int, new_status: ReportStatus) -> Optional[Report]:
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None

    # 이미 처리된 제보는 상태 변경 불가
    if db_report.status != ReportStatus.pending:
        raise ValueError(f"이미 '{db_report.status.value}' 상태인 제보는 변경할 수 없습니다.")

    db_report.status = new_status
    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now(timezone.utc)
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(db_report)
    except Exception:
        db.rollback()
        raise
    return db_report


def get_all_reports(db: Session, skip: int = 0, limit: int = 100, status: Optional[ReportStatus] = None) -> list[Report]:
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()