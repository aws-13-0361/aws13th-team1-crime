# 프로젝트 버그 수정 내역

## 1. run.py - 중복 엔드포인트 제거

**문제:** `GET /` 엔드포인트가 2개 정의되어 있어 하나만 동작함

```python
# 제거된 코드 (45~47행)
@app.get("/")
def root():
    return {"message": "API Server is running"}
```

---

## 2. router/report_router.py - prefix 및 경로 수정

**문제 1:** `prefix="/api"`로 설정되어 제보 CRUD 경로가 `/api`, `/api/{id}` 등 비정상적인 경로로 매핑됨

**문제 2:** 단건 조회 경로가 `@router.get("/reports/{report_id}")`로 되어 있어 `/api/reports/{id}` (다른 경로들과 불일치)

**문제 3:** 정렬이 2번 적용됨 (if/else로 정렬 후 다시 `.order_by(Report.created_at.desc())` 호출)

**문제 4:** `import datetime` 미사용

```python
# 수정 전
import datetime                    # 미사용
router = APIRouter(prefix="/api")  # 잘못된 prefix
@router.get("/reports/{report_id}")  # 불일치 경로
reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()  # 정렬 중복

# 수정 후
# import datetime 제거
router = APIRouter(prefix="/api/reports")
@router.get("/{report_id}")
reports = query.offset(skip).limit(limit).all()
```

---

## 3. router/admin_router.py - prefix 충돌 해결

**문제:** `prefix="/api"`로 설정되어 `GET /api/reports`가 report_router의 `GET /api/reports`와 충돌

```python
# 수정 전
router = APIRouter(prefix="/api", tags=["Admin"])

# 수정 후
router = APIRouter(prefix="/api/admin", tags=["Admin"])
```

**변경된 API 경로:**
| 기존 | 변경 후 |
|------|---------|
| `POST /api/reports/{id}/approve` | `POST /api/admin/reports/{id}/approve` |
| `POST /api/reports/{id}/reject` | `POST /api/admin/reports/{id}/reject` |
| `GET /api/reports` | `GET /api/admin/reports` |

---

## 4. services/official_service.py - 3가지 수정

### 4-1. Report import 누락 (서버 시작 불가)
```python
# 수정 전: Report가 import 되지 않아 NameError 발생
from models import Region, CrimeType

# 수정 후
from models import Region, CrimeType, Report
```

### 4-2. `from sqlalchemy import func` 중복 import 제거
```python
# 수정 전
from sqlalchemy import func    # 3행
from sqlalchemy import func    # 6행 (중복)

# 수정 후
from sqlalchemy import func    # 1번만
```

### 4-3. crime_type이 NULL일 때 AttributeError 방지
```python
# 수정 전: crime_type_id가 nullable인데 null 체크 없이 접근
{"crime_major": s.crime_type.major, "crime_minor": s.crime_type.minor, "count": s.count}

# 수정 후
{
    "crime_major": s.crime_type.major if s.crime_type else None,
    "crime_minor": s.crime_type.minor if s.crime_type else None,
    "count": s.count
}
```

---

## 5. services/report_service.py - 승인 시 통계 증분 누락

**문제:** 제보 승인 시 `official_stats` 테이블의 범죄 횟수가 증가하지 않음

```python
# 수정 후: 승인 처리 시 통계 업데이트 호출 추가
from services import official_service

if new_status == ReportStatus.approved:
    db_report.approved_at = datetime.now(timezone.utc)
    # 승인 시 범죄 통계 +1
    official_service.update_or_create_stat(db, db_report)
```

---

## 6. schemas/report.py - 중복 및 미사용 코드 정리

**문제 1:** `ReportStatus` enum이 `models/report.py`와 `schemas/report.py`에 중복 정의

**문제 2:** `field_validator`, `Enum` 미사용 import

**문제 3:** `class Config` (Pydantic v1 방식) → `model_config = ConfigDict(...)` (Pydantic v2) 통일

```python
# 수정 전
from pydantic import BaseModel, ConfigDict, field_validator  # field_validator 미사용
from enum import Enum                                         # Enum 미사용

class ReportStatus(str, Enum):  # models/report.py와 중복
    pending = "pending"
    ...

class ReportRead(BaseModel):
    class Config:               # Pydantic v1 방식
        from_attributes = True

# 수정 후
from pydantic import BaseModel, ConfigDict
from models.report import ReportStatus  # 모델에서 import

class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 방식
```

---

## 7. core/database.py - SSL 설정 하드코딩 수정

**문제:** SSL 인증서 경로를 동적으로 설정하는 코드가 있지만, 실제 엔진 생성 시 `{"fake_config": True}`로 하드코딩되어 무시됨

```python
# 수정 전: 동적 connect_args를 무시하고 하드코딩
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"ssl": {"fake_config": True}},  # 하드코딩
    ...
)

# 수정 후: 동적으로 구성된 connect_args 사용
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,  # 인증서 있으면 SSL, 없으면 일반 연결
    ...
)
```

---

## 8. router/auth_router.py - 하드코딩 URL 및 debug print 제거

**문제 1:** 로그인 후 리다이렉트 URL이 `"http://localhost:5173"`로 하드코딩

**문제 2:** `print()` debug 문이 운영 코드에 포함

```python
# 수정 전
print(f"DEBUG: Callback saved user_id: {user.id}")
print(f"DEBUG: Current Session: {request.session}")
response = RedirectResponse(url="http://localhost:5173")
...
print(f"DEBUG: Callback Error: {str(e)}")

# 수정 후
import logging
logger = logging.getLogger(__name__)

logger.info(f"Callback saved user_id: {user.id}")
response = RedirectResponse(url=settings.FRONTEND_URL)
...
logger.error(f"Callback Error: {str(e)}")
```

---

## 수정 파일 요약

| 파일 | 수정 내용 |
|------|-----------|
| `run.py` | 중복 `GET /` 엔드포인트 제거 |
| `router/report_router.py` | prefix 수정, 경로 통일, 정렬 중복 제거, 미사용 import 제거 |
| `router/admin_router.py` | prefix를 `/api/admin`으로 변경 (충돌 방지) |
| `router/auth_router.py` | 하드코딩 URL → `settings.FRONTEND_URL`, print → logging |
| `services/official_service.py` | Report import 추가, 중복 import 제거, null 체크 추가 |
| `services/report_service.py` | 승인 시 통계 증분 호출 추가 |
| `schemas/report.py` | 중복 ReportStatus 제거, 미사용 import 제거, Pydantic v2 통일 |
| `core/database.py` | SSL connect_args 하드코딩 → 동적 설정 사용 |
