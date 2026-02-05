from sqlalchemy.orm import Session
from models.report import Report, ReportStatus
from models.officialstat import OfficialStat          # 추가
from datetime import datetime, timezone
from typing import Optional
from models.user import User


def update_report_status(db: Session, report_id: int, new_status: ReportStatus) -> Optional[Report]:
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None

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


# ============================================================
# 새로 추가할 함수: 승인 시 범죄 횟수 +1
# ============================================================
def increment_crime_count(db: Session, report: Report):
    """
    승인된 제보의 region_id, crime_type_id를 기반으로
    official_stats 테이블의 해당 연도 범죄 횟수를 +1 합니다.
    """
    current_year = datetime.now().year

    # 1) 해당 지역 + 범죄유형 + 올해 데이터가 이미 있는지 조회
    stat = db.query(OfficialStat).filter(
        OfficialStat.region_id == report.region_id,
        OfficialStat.crime_type_id == report.crime_type_id,
        OfficialStat.year == current_year
    ).first()

    if stat:
        # 2-A) 이미 있으면 count를 +1
        stat.count += 1
    else:
        # 2-B) 없으면 새 레코드 생성 (count=1)
        new_stat = OfficialStat(
            region_id=report.region_id,
            crime_type_id=report.crime_type_id,
            year=current_year,
            count=1
        )
        db.add(new_stat)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise