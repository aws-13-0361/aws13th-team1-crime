from sqlalchemy.orm import Session
from models.report import Report, ReportStatus
from datetime import datetime


def update_report_status(db: Session, report_id: int, new_status: ReportStatus):
    # 1. 제보 찾기
    db_report = db.query(Report).filter(Report.id == report_id).first()

    if not db_report:
        return None

    # 2. 상태 업데이트
    db_report.status = new_status

    # 3. 상태에 따른 시간 기록
    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now()
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now()

    db.commit()
    db.refresh(db_report)
    return db_report