# 코드 리뷰 보고서

> 리뷰 일자: 2025-02-05 (2차) | 대상: 전체 프로젝트 소스 코드

---

## 1. 프로젝트 구조

```
FInalPJ/
├── run.py                    # FastAPI 앱 엔트리포인트
├── requirements.txt          # 의존성 목록
├── .env.exmaple              # 환경변수 예시 (파일명 오타)
├── core/
│   ├── config.py             # DB 설정 (환경변수 로딩)
│   └── database.py           # SQLAlchemy 엔진/세션/Base
├── models/
│   ├── __init__.py           # 모델 일괄 임포트
│   ├── user.py               # User 모델
│   ├── region.py             # Region 모델
│   ├── crime_type.py         # CrimeType 모델
│   ├── report.py             # Report 모델 + ReportStatus Enum
│   └── officialstat.py       # OfficialStat 모델
├── router/
│   ├── admin_router.py       # 관리자 API (승인/반려/목록)
│   ├── official_router.py    # 통계 조회 API
│   └── test_router.py        # (빈 파일)
├── schemas/
│   ├── report.py             # Report 관련 Pydantic 스키마
│   └── officialstat.py       # 통계 관련 Pydantic 스키마
├── services/
│   ├── report_service.py     # 제보 상태 변경/조회 로직
│   └── official_service.py   # 통계 조회 로직
└── utils/
    └── __init__.py           # (빈 파일)
```

---

## 2. 이전 리뷰(1차) 대비 수정 현황

| 1차 리뷰 항목 | 상태 | 비고 |
|---|---|---|
| BUG-01: `official_router` 미등록 | **수정 완료** | `run.py`에 등록됨 |
| BUG-02: 모델 미임포트로 `create_all()` 불완전 | **수정 완료** | `official_service`가 `models` 패키지를 임포트하면서 전체 모델 로드됨 |
| BUG-03: `models/__init__.py`에서 `OfficialStat` 누락 | **수정 완료** | 임포트 추가됨 |
| BUG-04: `RegionSchema.city`가 필수 필드 | **수정 완료** | `Optional[str] = None`으로 변경됨 |
| BUG-05: `city=None`일 때 `"서울 None"` 생성 | **수정 완료** | 삼항연산자로 분기 처리됨 |
| BUG-06: `ReportStatus` Enum 이중 정의 | **수정 완료** | `schemas/report.py`가 `models.report.ReportStatus`를 재사용 |
| BUG-07: 미사용 임포트 `offset_from_tz_string` | **수정 완료** | 제거됨 |
| BUG-08: SSL `"fake_config": True` | **수정 완료** | 인증서 파일 존재 여부에 따른 동적 SSL 구성으로 개선 |

---

## 3. 치명적 버그 (Critical)

### BUG-C01: `official_router.py`에서 `city`가 필수 파라미터

- **파일**: `router/official_router.py:15`
- **심각도**: Critical
- **설명**: `get_stats()` 함수에서 `city: str`로 선언되어 있어 **필수 쿼리 파라미터**임. 시/도 단위(예: "세종")처럼 city가 없는 지역은 이 API를 호출할 수 없음. `official_service.py`에서 `city=None` 처리를 추가했지만, 라우터에서 city가 필수이므로 **서비스 쪽 수정이 사실상 무의미**함.

```python
# 현재 (city 필수 - None이 전달될 수 없음)
def get_stats(
    province: str,
    city: str,           # <-- 필수 파라미터
    ...
):

# 수정 필요
def get_stats(
    province: str,
    city: str = None,    # <-- 선택 파라미터로 변경
    ...
):
```

### BUG-C02: `models/officialstat.py`에서 `crime_type_id`가 `NOT NULL`

- **파일**: `models/officialstat.py:10`
- **심각도**: Critical
- **설명**: README의 SQL DDL에서는 `crime_type_id INT NULL` (합계 데이터용으로 NULL 허용)이지만, SQLAlchemy 모델에서는 `nullable=False`로 설정됨. 범죄 유형 전체 합계 행을 저장할 수 없어 데이터 불일치 발생.

```python
# 현재 (NULL 불허)
crime_type_id = Column(Integer, ForeignKey("crime_types.id"), nullable=False)

# README DDL 기준 수정 필요
crime_type_id = Column(Integer, ForeignKey("crime_types.id"), nullable=True)
```

---

## 4. 주요 버그 (Major)

### BUG-M01: `admin_router.py`에서 `ReportStatus` 이중 임포트 (데드 코드)

- **파일**: `router/admin_router.py:5,7`
- **심각도**: Major
- **설명**: 5번째 줄에서 `from schemas.report import ReportResponse, ReportStatus`로 임포트한 뒤, 7번째 줄에서 `from models.report import ReportStatus`로 덮어씀. 5번째 줄의 `ReportStatus` 임포트는 사용되지 않는 데드 코드.

```python
# 현재 (ReportStatus 이중 임포트)
from schemas.report import ReportResponse, ReportStatus  # <-- ReportStatus 쓸모 없음
from models.report import ReportStatus                    # <-- 이것이 실제 사용됨

# 수정 필요
from schemas.report import ReportResponse
from models.report import ReportStatus
```

### BUG-M02: `schemas/report.py`에서 `Enum` 미사용 임포트

- **파일**: `schemas/report.py:3`
- **심각도**: Minor
- **설명**: `from enum import Enum`을 임포트하지만, `ReportStatus`를 자체 정의하지 않고 `models.report`에서 가져오므로 이 임포트는 사용되지 않음.

### BUG-M03: `official_service.py`에서 함수 내부 import

- **파일**: `services/official_service.py:17`
- **심각도**: Minor
- **설명**: `from sqlalchemy import func`가 `fetch_official_stats()` 함수 내부에서 임포트됨. PEP 8 컨벤션에 따라 파일 상단으로 이동 권장.

### BUG-M04: `official_service.py`에서 불필요한 필터 조건

- **파일**: `services/official_service.py:69`
- **심각도**: Minor
- **설명**: `.filter(CrimeType.major.isnot(None))` 조건이 있지만, `CrimeType.major`는 DB 모델에서 `nullable=False`이므로 이 필터는 항상 참이라 의미 없음. 의도가 `CrimeType.minor.isnot(None)`이었을 가능성 있음 (합계 행 제외 목적).

```python
# 현재 (무의미한 필터)
.filter(CrimeType.major.isnot(None))

# 혹시 의도한 것이 중분류가 있는 항목만 반환이었다면:
.filter(CrimeType.minor.isnot(None))
```

### BUG-M05: `Region.official_stat` relationship 네이밍

- **파일**: `models/region.py:14`, `models/officialstat.py:15`
- **심각도**: Minor
- **설명**: 1:N 관계인데 relationship 이름이 `official_stat` (단수형). 컨벤션상 `official_stats` (복수형)이 적절.

### BUG-M06: `core/database.py`에서 `print()` 사용

- **파일**: `core/database.py:13,16`
- **심각도**: Minor
- **설명**: SSL 적용 여부를 `print()`로 출력하고 있음. 프로덕션 환경에서는 Python `logging` 모듈 사용 권장.

### BUG-M07: `ReportStatusUpdate` 스키마 미사용

- **파일**: `schemas/report.py:13-21`
- **심각도**: Minor
- **설명**: `ReportStatusUpdate` 클래스가 정의되어 있지만 어디서도 사용되지 않음. 데드 코드.

---

## 5. 보안 이슈 (Security)

### SEC-01: 인증/인가 미들웨어 없음

- **심각도**: **High**
- **설명**: 관리자 API(`/api/admin/reports/*`)에 인증/인가 검증이 전혀 없음. 누구나 URL만 알면 제보를 승인/반려 가능. 통계 API도 동일하게 인증 없이 접근 가능.
- **현재 상태**: `requirements.txt`에 `PyJWT`, `passlib[bcrypt]` 등 인증 관련 패키지가 이미 설치되어 있으나 코드에서 사용하지 않음.
- **수정 방안**: JWT 기반 인증 미들웨어 구현 필요.

```python
# 예시: FastAPI Depends를 활용한 인증
from fastapi import Depends, Security

def get_current_user(token: str = Depends(oauth2_scheme)):
    # JWT 토큰 검증 로직
    ...

def require_admin(user = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return user

# 라우터에 적용
@router.post("/reports/{report_id}/approve")
def approve_report(report_id: int, admin=Depends(require_admin), db=Depends(get_db)):
    ...
```

### SEC-02: CORS 설정 없음

- **심각도**: **Medium**
- **설명**: 프론트엔드에서 이 API를 호출하면 브라우저 CORS 정책에 의해 차단됨.

```python
# run.py에 추가 필요
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["허용할_프론트엔드_도메인"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### SEC-03: DB 접속 정보 Null 검증 없음

- **파일**: `core/config.py:9,12`
- **심각도**: **Low**
- **설명**: `DB_PASSWORD`와 `DB_NAME`에 기본값이 없음. `.env` 파일이 없거나 이 값들이 누락되면 `mysql+pymysql://admin:None@localhost:3306/None` 같은 잘못된 URL이 생성되어 서버 시작 시 불명확한 에러 발생.

---

## 6. 코드 품질 이슈 (Code Quality)

### CQ-01: `declarative_base()` Deprecated

- **파일**: `core/database.py:3,25`
- **설명**: SQLAlchemy 2.0에서 `from sqlalchemy.ext.declarative import declarative_base`는 deprecated. 향후 제거 예정.

```python
# 현재 (deprecated)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# SQLAlchemy 2.0+ 권장
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

### CQ-02: Pydantic Config 스타일 혼용

- **파일**: `schemas/report.py` vs `schemas/officialstat.py`
- **설명**: `schemas/report.py`는 Pydantic v2 방식(`model_config = ConfigDict(from_attributes=True)`)을 사용하고, `schemas/officialstat.py`는 v1 방식(`class Config: from_attributes = True`)을 사용. 하나의 스타일로 통일 권장.

### CQ-03: `requirements.txt`에 미사용 패키지 포함

- **파일**: `requirements.txt`
- **설명**: 아래 패키지들이 설치되지만 코드에서 사용되지 않음:

| 패키지 | 용도 | 사용 여부 |
|---|---|---|
| `pydantic-settings` | 환경변수 관리 (BaseSettings) | 미사용 (`os.getenv` 직접 사용) |
| `alembic` | DB 마이그레이션 | 미사용 (alembic.ini 없음) |
| `DBUtils` | DB 커넥션 풀링 | 미사용 |
| `filelock` | 파일 잠금 | 미사용 |

### CQ-04: `.env.exmaple` 파일명 오타

- `.env.exmaple` -> `.env.example`로 수정 필요.

### CQ-05: `test_router.py`, `utils/__init__.py` 빈 파일

- 향후 구현 예정이라면 TODO 주석 추가 권장.

---

## 7. 문서와 코드 불일치

| 항목 | README 기획 | 실제 구현 |
|---|---|---|
| `official_stats.crime_type_id` | `NULL` 허용 (합계 데이터용) | `nullable=False` (합계 저장 불가) |
| `official_stats.last_updated` 컬럼 | SQL DDL에 없음 | 모델에 존재 |
| 인증 API (register/login/logout) | 기획됨 | 미구현 |
| 제보 CRUD (상세/작성/수정/삭제) | 기획됨 | 미구현 (조회만 존재) |
| `official_stats.id` 타입 | `BIGINT` | 모델에서 `Integer` 사용 |

---

## 8. 구현 완료 현황

| 기능 | 상태 | 비고 |
|---|---|---|
| DB 모델 정의 (5개 테이블) | **완료** | DDL 대비 일부 불일치 존재 |
| 관리자 승인 API | **완료** | 인증 없음 |
| 관리자 반려 API | **완료** | 인증 없음 |
| 관리자 목록 조회 API | **완료** | 상태 필터/페이징 지원 |
| 통계 조회 API | **완료** | `city` 필수 파라미터 문제 |
| 지역 목록 API | **완료** | - |
| 범죄 유형 목록 API | **완료** | 불필요한 필터 존재 |
| 회원가입/로그인/로그아웃 | 미구현 | 패키지는 설치됨 |
| 제보 CRUD (작성/상세/수정/삭제) | 미구현 | - |
| CORS 미들웨어 | 미구현 | - |
| 인증/인가 미들웨어 | 미구현 | - |

---

## 9. 즉시 수정 권장 (우선순위 순)

### 우선순위 1: 동작 오류 수정
1. `official_router.py`의 `city` 파라미터를 선택값(`str = None`)으로 변경 (BUG-C01)
2. `models/officialstat.py`의 `crime_type_id`를 `nullable=True`로 변경 (BUG-C02)
### 우선순위 2: 코드 정리
4. `admin_router.py`의 이중 임포트 정리 (BUG-M01)
5. `schemas/report.py`의 미사용 `Enum` 임포트 제거 (BUG-M02)
6. `official_service.py`의 함수 내부 import를 파일 상단으로 이동 (BUG-M03)
7. `official_service.py:69`의 불필요한 필터 확인 및 수정 (BUG-M04)
8. `.env.exmaple` -> `.env.example` 파일명 수정 (CQ-04)

### 우선순위 3: 보안 강화
9. 인증/인가 미들웨어 구현 (SEC-01)
10. CORS 미들웨어 추가 (SEC-02)

### 우선순위 4: 장기 개선
11. `declarative_base()` -> `DeclarativeBase` 전환 (CQ-01)
12. Pydantic Config 스타일 통일 (CQ-02)
13. 미사용 패키지 정리 (CQ-03)
14. `print()` -> `logging` 전환 (BUG-M06)

---

## 10. 잘된 점

- **계층 분리**: Router - Service - Model 3계층 구조가 잘 갖춰져 있음
- **상태 전이 검증**: `report_service.py`에서 pending 상태만 변경 가능하도록 검증하는 로직이 적절함
- **에러 핸들링**: `admin_router.py`에서 `ValueError` -> 409, `None` -> 404 분기 처리가 명확함
- **트랜잭션 관리**: `report_service.py`에서 `commit/rollback` 패턴이 올바르게 구현됨
- **1차 리뷰 반영**: 8개 치명적/주요 버그 중 8개 모두 수정 완료 (대응 속도 우수)
- **SSL 동적 구성**: `database.py`에서 인증서 존재 여부에 따라 SSL 적용 여부를 분기하는 방식이 실용적임
- **페이징 처리**: `admin_router.py`에서 `skip/limit` 파라미터에 적절한 검증(`ge=0`, `ge=1, le=500`) 적용
