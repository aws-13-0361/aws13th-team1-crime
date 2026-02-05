import logging

from sqlalchemy.orm import Session
from models.report import Report, ReportStatus
from models.officialstat import OfficialStat          # 추가
from datetime import datetime, timezone
from typing import Optional
from services import official_service

logger = logging.getLogger(__name__)


def update_report_status(db: Session, report_id: int, new_status: ReportStatus) -> Optional[Report]:
    logger.info(f"--- [제보 승인 프로세스 시작] ID: {report_id} ---")

    # 1. 제보 존재 여부 확인
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        logger.warning(f"ID {report_id}에 해당하는 제보를 찾을 수 없습니다.")
        return None

    if db_report.status != ReportStatus.pending:
        raise ValueError(f"이미 '{db_report.status.value}' 상태인 제보는 변경할 수 없습니다.")

    # 3. 비즈니스 로직 수행
    if new_status == ReportStatus.approved:
        logger.info(f"제보 승인 처리 중... 지역 ID: {db_report.region_id}")
        db_report.status = ReportStatus.approved  # 명시적 상태 변경
        db_report.approved_at = datetime.now(timezone.utc)

        # 통계 데이터 업데이트 및 ID 연결
        stat_id = official_service.update_or_create_stat(db, db_report)
        db_report.official_stat_id = stat_id
        logger.info(f"통계 테이블 반영 완료 (Stat ID: {stat_id})")
    #eeee
    elif new_status == ReportStatus.rejected:
        logger.info(f"제보 거절 처리 중... ID: {report_id}")
        db_report.status = ReportStatus.rejected
        db_report.rejected_at = datetime.now(timezone.utc)

    # 4. 트랜잭션 확정ddd
    try:
        db.commit()
        logger.info(f"✅ DB 커밋 성공: 제보 {report_id} 상태가 {new_status.value}로 변경되었습니다.")
        db.refresh(db_report)
    except Exception as e:
        db.rollback()
        logger.error(f"❌ DB 커밋 실패 (롤백 수행): {e}")
        raise e

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


def get_all_reports(db: Session, skip: int = 0, limit: int = 100, status: Optional[ReportStatus] = None) -> list[Report]:
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()