# 관리자 검수 API 코드리뷰

> **리뷰 일시**: 2026-02-05
> **리뷰 대상**: 관리자 검수 API 엔드포인트 3개 (`approve`, `reject`, `get_reports`)
> **대상 파일**: `app/admin_router.py`, `services/report_service.py`, `schemas/report.py`, `models/report.py`, `models/user.py`, `core/database.py`, `run.py`

---

## 요약

관리자 검수 API는 제보(Report)의 승인/반려/목록조회 기능을 제공합니다. 전반적인 구조(라우터 → 서비스 → 모델)는 올바르게 분리되어 있으나, **인증/인가 부재**, **에러 처리 누락**, **라우터 prefix 중복** 등 운영 환경 배포 전 반드시 수정해야 할 이슈가 다수 발견되었습니다.

| 심각도 | 건수 |
|--------|------|
| Critical | 4 |
| Warning | 6 |
| Info | 3 |

---

## Critical Issues

### 1. 인증/인가 미적용

**파일**: `app/admin_router.py` 전체
**심각도**: Critical

관리자 전용 엔드포인트임에도 어떠한 인증(Authentication) 및 인가(Authorization) 검증이 없습니다. 현재 상태에서는 누구나 제보를 승인/반려할 수 있습니다.

**현재 코드**:
```python
# app/admin_router.py:12-26
@router.post("/reports/{report_id}/approve", response_model=ReportResponse)
def approve_report(report_id: int, db: Session = Depends(get_db)):
    updated_report = report_service.update_report_status(
        db=db, report_id=report_id, new_status=ReportStatus.approved
    )
    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")
    return updated_report
```

**수정 제안**:
```python
from core.auth import get_current_admin_user  # 관리자 인증 의존성

@router.post("/reports/{report_id}/approve", response_model=ReportResponse)
def approve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),  # 인증+인가
):
    updated_report = report_service.update_report_status(
        db=db, report_id=report_id, new_status=ReportStatus.approved
    )
    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")
    return updated_report
```

> `models/user.py`에 이미 `UserRole.admin`이 정의되어 있으므로, JWT 토큰에서 사용자 role을 확인하는 `get_current_admin_user` 의존성을 구현하면 됩니다.

---

### 2. reject 엔드포인트 404 미처리

**파일**: `app/admin_router.py:28-30`
**심각도**: Critical

`approve_report`는 `None` 체크 후 404를 반환하지만, `reject_report`는 서비스 반환값이 `None`이어도 그대로 반환합니다. 존재하지 않는 report_id로 요청하면 `null` 응답이 되거나 직렬화 오류가 발생합니다.

**현재 코드**:
```python
# app/admin_router.py:28-30
@router.post("/reports/{report_id}/reject")
def reject_report(report_id: int, db: Session = Depends(get_db)):
    return report_service.update_report_status(db, report_id, ReportStatus.rejected)
```

**수정 제안**:
```python
@router.post("/reports/{report_id}/reject", response_model=ReportResponse)
def reject_report(report_id: int, db: Session = Depends(get_db)):
    updated_report = report_service.update_report_status(db, report_id, ReportStatus.rejected)
    if not updated_report:
        raise HTTPException(status_code=404, detail="해당 제보를 찾을 수 없습니다.")
    return updated_report
```

---

### 3. 중복 승인/반려 방지 없음

**파일**: `services/report_service.py:6-24`
**심각도**: Critical

이미 `approved` 또는 `rejected` 상태인 제보를 다시 승인/반려할 수 있습니다. 상태 전이 규칙이 없어 데이터 무결성이 깨질 수 있습니다 (예: `approved_at`과 `rejected_at`이 동시에 존재).

**현재 코드**:
```python
# services/report_service.py:6-24
def update_report_status(db: Session, report_id: int, new_status: ReportStatus):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None
    db_report.status = new_status
    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now()
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now()
    db.commit()
    db.refresh(db_report)
    return db_report
```

**수정 제안**:
```python
def update_report_status(db: Session, report_id: int, new_status: ReportStatus):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        return None

    # 이미 처리된 제보는 상태 변경 불가
    if db_report.status != ReportStatus.pending:
        raise ValueError(f"이미 '{db_report.status.value}' 상태인 제보는 변경할 수 없습니다.")

    db_report.status = new_status
    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now()
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now()
    db.commit()
    db.refresh(db_report)
    return db_report
```

> 라우터에서 `ValueError`를 잡아 `HTTPException(status_code=409)` 등으로 변환하는 처리가 필요합니다.

---

### 4. DB 트랜잭션 에러 처리 없음

**파일**: `services/report_service.py:22`
**심각도**: Critical

`db.commit()` 실패 시 rollback이 없습니다. 커밋 실패(예: DB 연결 끊김, 제약 조건 위반) 시 세션이 비정상 상태로 남을 수 있습니다.

**현재 코드**:
```python
# services/report_service.py:22-23
    db.commit()
    db.refresh(db_report)
```

**수정 제안**:
```python
    try:
        db.commit()
        db.refresh(db_report)
    except Exception:
        db.rollback()
        raise
```

> `core/database.py`의 `get_db()`에서 `finally: db.close()`는 세션을 닫지만, 커밋 실패 후의 dirty 상태를 명시적으로 rollback하지 않으므로 서비스 레이어에서 처리하는 것이 안전합니다.

---

## Warning Issues

### 5. 라우터 prefix 중복

**파일**: `app/admin_router.py:8` + `run.py:19`
**심각도**: Warning

`admin_router` 내부에서 `prefix="/api/admin"`을 지정하고, `run.py`에서 `include_router` 시에도 `prefix="/api/admin"`을 지정합니다. 결과적으로 실제 API 경로가 다음과 같이 됩니다:

- 의도한 경로: `/api/admin/reports`
- **실제 경로**: `/api/admin/api/admin/reports`

**현재 코드**:
```python
# app/admin_router.py:8
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# run.py:19
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
```

**수정 제안** (둘 중 하나 선택):

방법 A — 라우터에서 prefix 제거:
```python
# app/admin_router.py:8
router = APIRouter(tags=["Admin"])

# run.py:19 (유지)
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
```

방법 B — run.py에서 prefix 제거:
```python
# app/admin_router.py:8 (유지)
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# run.py:19
app.include_router(admin_router, tags=["Admin"])
```

---

### 6. ReportResponse에 rejected_at 누락

**파일**: `schemas/report.py:28-35`
**심각도**: Warning

`models/report.py`에는 `rejected_at` 컬럼이 정의되어 있지만, `ReportResponse` 스키마에는 `approved_at`만 포함되어 있습니다. 반려된 제보의 반려 시각을 클라이언트에서 확인할 수 없습니다.

**현재 코드**:
```python
# schemas/report.py:28-35
class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

**수정 제안**:
```python
class ReportResponse(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None  # 추가

    model_config = ConfigDict(from_attributes=True)
```

---

### 7. import 중복

**파일**: `app/admin_router.py:6, 32`
**심각도**: Warning

`from typing import List`가 파일 상단(6행)과 중간(32행)에서 두 번 임포트되어 있습니다.

**현재 코드**:
```python
# app/admin_router.py:6
from typing import List

# app/admin_router.py:32
from typing import List # 상단에 추가 필요
```

**수정 제안**: 32행의 중복 import를 삭제합니다.

---

### 8. datetime.now() vs datetime.utcnow()

**파일**: `services/report_service.py:18, 20`
**심각도**: Warning

`datetime.now()`는 서버의 로컬 시간대를 사용합니다. 서버가 다른 시간대에 배포될 경우 시각 데이터의 일관성이 깨질 수 있습니다.

**현재 코드**:
```python
# services/report_service.py:17-20
    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now()
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now()
```

**수정 제안**:
```python
from datetime import datetime, timezone

    if new_status == ReportStatus.approved:
        db_report.approved_at = datetime.now(timezone.utc)
    elif new_status == ReportStatus.rejected:
        db_report.rejected_at = datetime.now(timezone.utc)
```

> `datetime.utcnow()`도 가능하지만 Python 3.12부터 deprecated 예정이므로, `datetime.now(timezone.utc)`를 권장합니다.

---

### 9. 목록 API에 status 필터 없음

**파일**: `app/admin_router.py:34-37`, `services/report_service.py:26-28`
**심각도**: Warning

관리자가 검수 대기(`pending`) 상태의 제보만 조회하는 기능이 없습니다. 전체 목록만 반환하므로 운영 시 불편하고, 불필요한 데이터 전송이 발생합니다.

**현재 코드**:
```python
# services/report_service.py:26-28
def get_all_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
```

**수정 제안**:
```python
def get_all_reports(db: Session, skip: int = 0, limit: int = 100, status: ReportStatus = None):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
```

---

### 10. limit 파라미터 상한 없음

**파일**: `app/admin_router.py:35`
**심각도**: Warning

`limit` 파라미터에 상한이 없어, `limit=999999` 같은 요청이 들어오면 전체 DB 스캔이 발생할 수 있습니다.

**현재 코드**:
```python
# app/admin_router.py:35
def get_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
```

**수정 제안**:
```python
from fastapi import Query

def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
```

---

## Info Issues

### 11. 비동기(async) 미사용

**파일**: `app/admin_router.py` 전체
**심각도**: Info

FastAPI는 `async def`를 통한 비동기 처리를 지원하지만, 모든 엔드포인트가 동기 `def`로 구현되어 있습니다. 현재 SQLAlchemy 동기 세션을 사용하고 있으므로 즉시 문제가 되지는 않지만, 향후 비동기 DB 드라이버(`asyncpg` 등)로 전환 시 개선을 고려할 수 있습니다.

---

### 12. status 컬럼 인덱스 없음

**파일**: `models/report.py:22`
**심각도**: Info

`status` 컬럼에 인덱스가 설정되어 있지 않습니다. 데이터가 많아지고 status 기반 필터링이 추가될 경우 쿼리 성능이 저하될 수 있습니다.

**현재 코드**:
```python
# models/report.py:22
status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.pending)
```

**수정 제안**:
```python
status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.pending, index=True)
```

---

### 13. 타입 힌트 미흡

**파일**: `services/report_service.py` 전체
**심각도**: Info

서비스 함수들의 반환 타입이 명시되어 있지 않습니다. 코드 가독성과 IDE 지원을 위해 타입 힌트를 추가하면 좋습니다.

**현재 코드**:
```python
def update_report_status(db: Session, report_id: int, new_status: ReportStatus):
def get_all_reports(db: Session, skip: int = 0, limit: int = 100):
```

**수정 제안**:
```python
from typing import Optional

def update_report_status(db: Session, report_id: int, new_status: ReportStatus) -> Optional[Report]:
def get_all_reports(db: Session, skip: int = 0, limit: int = 100) -> list[Report]:
```

---

## 잘된 점

1. **계층 분리**: 라우터(Router) → 서비스(Service) → 모델(Model) → 스키마(Schema)로 관심사가 적절히 분리되어 있습니다.
2. **Pydantic v2 활용**: `model_config = ConfigDict(from_attributes=True)`로 최신 Pydantic v2 방식을 사용하고 있습니다.
3. **field_validator 적용**: `ReportStatusUpdate`에서 입력값을 소문자로 정규화하는 유효성 검증이 잘 되어 있습니다.
4. **DB 세션 의존성 주입**: `get_db()`를 `Depends()`로 주입하는 FastAPI 표준 패턴을 따르고 있습니다.
5. **최신순 정렬**: 목록 조회 시 `created_at.desc()`로 최신순 정렬을 기본 적용하고 있습니다.
6. **Enum 기반 상태 관리**: 문자열 대신 `Enum`으로 상태를 관리하여 오타나 잘못된 값 입력을 방지합니다.

---

## 전체 개선 제안 (우선순위순)

| 순위 | 작업 | 심각도 | 예상 난이도 |
|------|------|--------|------------|
| 1 | 인증/인가 미들웨어 추가 (JWT + role 검증) | Critical | 중 |
| 2 | reject 엔드포인트 404 처리 추가 | Critical | 하 |
| 3 | 라우터 prefix 중복 수정 | Warning | 하 |
| 4 | 중복 상태 변경 방지 로직 추가 | Critical | 하 |
| 5 | DB 트랜잭션 rollback 처리 추가 | Critical | 하 |
| 6 | import 중복 제거 | Warning | 하 |
| 7 | ReportResponse에 rejected_at 필드 추가 | Warning | 하 |
| 8 | datetime.now() → datetime.now(timezone.utc) | Warning | 하 |
| 9 | status 필터 파라미터 추가 | Warning | 중 |
| 10 | limit 상한 설정 | Warning | 하 |
| 11 | 서비스 함수 반환 타입 힌트 추가 | Info | 하 |
| 12 | status 컬럼 인덱스 추가 | Info | 하 |
| 13 | 비동기 전환 검토 | Info | 상 |
