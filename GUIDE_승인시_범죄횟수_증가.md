# 관리자 승인 시 범죄 횟수 자동 증가 구현 가이드

## 현재 상태 분석

### 현재 승인 흐름
```
사용자 제보 등록 → 관리자 승인/거절 → 상태만 변경 (끝)
```

### 목표 흐름
```
사용자 제보 등록 → 관리자 승인 → 상태 변경 + official_stats 범죄 횟수 +1
```

### 핵심 연결 고리
Report 테이블의 `region_id`와 `crime_type_id`가 OfficialStat 테이블의 같은 컬럼과 매칭됩니다.

```
Report (제보)                    OfficialStat (범죄 통계)
├── region_id ─────────────────→ region_id
├── crime_type_id ─────────────→ crime_type_id
└── status (approved)           └── count (이걸 +1 해야 함)
```

---

## 수정해야 할 파일 (총 2개)

| 순서 | 파일 | 변경 내용 |
|------|------|----------|
| 1 | `services/report_service.py` | 범죄 횟수 증가 함수 추가 |
| 2 | `router/admin_router.py` | 승인 시 범죄 횟수 증가 함수 호출 |

---

## Step 1: `services/report_service.py` 수정

### 변경 전 (현재 코드)
```python
from sqlalchemy.orm import Session
from models.report import Report, ReportStatus
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
```

### 변경 후 (수정된 코드)
```python
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
```

### 변경 요약
- `OfficialStat` 모델 import 추가 (1줄)
- `increment_crime_count()` 함수 신규 추가
- 기존 `update_report_status()` 함수는 변경 없음

---

## Step 2: `router/admin_router.py` 수정

### 변경 전 (현재 코드)
```python
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
```

### 변경 후 (수정된 코드)
```python
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

    # ====== 추가: 승인 성공 시 범죄 횟수 +1 ======
    try:
        report_service.increment_crime_count(db=db, report=updated_report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"범죄 통계 업데이트 실패: {str(e)}")
    # =============================================

    return updated_report
```

### 변경 요약
- `approve_report()` 함수 안에 `increment_crime_count()` 호출 3줄 추가
- `reject_report()`는 변경 없음 (거절 시에는 횟수 올리지 않음)

---

## 동작 흐름 정리

```
1. 관리자가 POST /api/admin/reports/5/approve 호출

2. update_report_status() 실행
   └── reports 테이블: status → "approved", approved_at → 현재시간

3. increment_crime_count() 실행
   └── official_stats 테이블에서 조회:
       WHERE region_id = (제보의 region_id)
         AND crime_type_id = (제보의 crime_type_id)
         AND year = 2026

   ├── 레코드 있음 → count += 1
   └── 레코드 없음 → 새 레코드 INSERT (count=1)

4. 응답 반환: 승인된 제보 정보
```

---

## 테스트 방법

### 1. 제보 등록
```bash
curl -X POST http://localhost:8000/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 제보",
    "content": "테스트 내용",
    "region_id": 1,
    "crime_type_id": 1,
    "user_id": 1
  }'
```

### 2. 승인 전 통계 확인
```bash
curl "http://localhost:8000/api/stats?province=서울&city=종로구"
# → count 값 확인 (예: 100)
```

### 3. 관리자 승인
```bash
curl -X POST http://localhost:8000/api/admin/reports/1/approve
```

### 4. 승인 후 통계 확인
```bash
curl "http://localhost:8000/api/stats?province=서울&city=종로구"
# → count 값이 +1 되었는지 확인 (예: 101)
```

---

## DB 직접 확인 (MySQL)
```sql
-- 승인 전후 비교
SELECT region_id, crime_type_id, year, count
FROM official_stats
WHERE region_id = 1 AND crime_type_id = 1 AND year = 2026;
```

---

## 주의사항

1. **중복 승인 방지**: `update_report_status()`에서 이미 `pending` 상태가 아니면 에러를 발생시키므로, 같은 제보가 두 번 승인되어 count가 2번 올라가는 일은 없습니다.

2. **거절 시에는 미반영**: `reject_report()`에는 `increment_crime_count()`를 호출하지 않으므로 거절된 제보는 통계에 영향을 주지 않습니다.

3. **연도 기준**: `datetime.now().year`를 사용하므로 승인 시점의 연도 기준으로 통계가 쌓입니다.
