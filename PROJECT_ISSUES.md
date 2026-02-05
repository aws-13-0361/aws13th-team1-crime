# 프로젝트 코드 분석 - 문제점 리포트

> 분석 일시: 2026-02-05
> 대상: `/Users/paek/Desktop/Project/01_AWS_13th/Web/FInalPJ`

---

## 1. 보안 (CRITICAL)

### 1-1. SessionMiddleware 시크릿키 하드코딩

- **파일**: `run.py:13`
- **현재 코드**:
  ```python
  secret_key="your-very-secret-key-here"
  ```
- **문제**: `config.py`에 `SESSION_SECRET_KEY`를 이미 정의해놓았지만 사용하지 않고, 추측 가능한 문자열을 그대로 사용 중. 세션 위조 공격에 노출됨.
- **수정 방향**: `settings.SESSION_SECRET_KEY`를 사용하도록 변경.

---

### 1-2. CORS 설정이 localhost로 고정

- **파일**: `run.py:21`
- **현재 코드**:
  ```python
  allow_origins=["http://localhost:5173","http://127.0.0.1:5173"]
  ```
- **문제**: 배포 환경에서 프론트엔드 도메인이 다르면 API 호출이 전부 CORS 에러로 차단됨.
- **수정 방향**: 환경변수로 관리하여 배포 시 실제 도메인 반영.

---

### 1-3. Admin 라우터에 인증/권한 검증 없음

- **파일**: `router/admin_router.py` (전체)
- **문제**: 승인(`/approve`), 거부(`/reject`), 목록 조회 API에 어떤 인증도 없음. **누구나** 제보를 승인/거부 가능.
- **수정 방향**: `get_current_user` 의존성 + `role == admin` 검증 추가.

---

### 1-4. Report CRUD에 인증/권한 검증 없음

- **파일**: `router/report_router.py` (수정/삭제 엔드포인트)
- **문제**: 제보 작성/수정/삭제에 로그인 사용자 확인이 없음. 아무나 타인의 제보를 수정/삭제 가능.
- **수정 방향**: 작성 시 세션의 `user_id` 사용, 수정/삭제 시 소유자 확인 로직 추가.

---

### 1-5. 에러 메시지에 내부 예외 정보 노출

- **파일**: `report_router.py:96`, `report_router.py:186`
- **현재 코드**:
  ```python
  detail=f"제보 저장 중 오류가 발생했습니다: {str(e)}"
  ```
- **문제**: DB 에러 등 내부 구현 정보가 클라이언트에 그대로 전달됨. 공격자에게 시스템 정보 제공.
- **수정 방향**: 로그에만 상세 에러를 기록하고, 클라이언트에는 일반적 메시지만 반환.

---

## 2. 버그 / 동작 오류

### 2-1. User 모델 `password_hash`가 NOT NULL인데 Google 로그인 시 None 할당

- **파일**: `models/user.py:18`, `services/auth_service.py:97`
- **User 모델**:
  ```python
  password_hash = Column(String(255), nullable=False)
  ```
- **Google 사용자 생성**:
  ```python
  new_user = User(
      ...
      password_hash=None,  # NOT NULL 제약 위반!
  )
  ```
- **결과**: Google OAuth 신규 사용자 가입 시 **DB INSERT 실패** (IntegrityError).
- **수정 방향**: `password_hash`를 `nullable=True`로 변경하거나, 기본값(빈 문자열 등) 설정.

---

### 2-2. `get_report` 단건 조회에서 None 처리 누락

- **파일**: `report_router.py:58-63`
- **문제**: 해당 ID의 제보가 없으면 `None`을 반환하는데, `response_model=ReportRead` 때문에 Pydantic 직렬화 에러 발생.
- **수정 방향**: `if not report: raise HTTPException(404, ...)` 추가.

---

### 2-3. `CrimeTypeSimple.minor`가 필수 필드인데 DB에서는 nullable

- **파일**: `schemas/report.py:22`, `models/crime_type.py:11`
- **스키마**:
  ```python
  class CrimeTypeSimple(BaseModel):
      minor: str  # 필수!
  ```
- **모델**:
  ```python
  minor = Column(String(50), nullable=True)  # NULL 허용
  ```
- **결과**: DB에서 `minor`가 NULL인 레코드를 읽으면 Pydantic 직렬화 오류 발생.
- **수정 방향**: `minor: Optional[str] = None`으로 변경.

---

### 2-4. Pydantic v2 모델 직접 속성 수정

- **파일**: `report_router.py:83`
- **현재 코드**:
  ```python
  report_data.crime_type_id = ai_crime_type_id
  ```
- **문제**: Pydantic v2 모델은 기본적으로 불변(frozen). 직접 속성 변경 시 `ValidationError` 발생 가능.
- **수정 방향**: `report_data.model_copy(update={"crime_type_id": ai_crime_type_id})` 사용.

---

### 2-5. 라우터 경로 충돌 (중복 등록)

- **파일**: `run.py:38-43` + `router/official_router.py:50-55`
- **중복 경로**:
  - `GET /api/regions` - `run.py`와 `official_router.py` 둘 다 정의
  - `GET /api/crime-types` - `run.py`와 `official_router.py` 둘 다 정의
- **결과**: 먼저 등록된 라우터가 우선하여, 의도하지 않은 핸들러가 호출될 수 있음.
- **수정 방향**: `run.py`의 중복 엔드포인트 제거.

---

## 3. 구조 / 설계 문제

### 3-1. `declarative_base()` 사용 (Deprecated)

- **파일**: `core/database.py:30`
- **현재 코드**:
  ```python
  from sqlalchemy.ext.declarative import declarative_base
  Base = declarative_base()
  ```
- **문제**: SQLAlchemy 2.0에서 deprecated. 향후 버전에서 제거 예정.
- **수정 방향**: `sqlalchemy.orm.DeclarativeBase` 사용.

---

### 3-2. `echo=True`가 항상 활성화

- **파일**: `core/database.py:26`
- **문제**: 모든 SQL 쿼리가 콘솔에 출력됨. 프로덕션에서 성능 저하 및 로그 과잉 유발.
- **수정 방향**: 환경변수로 제어하거나 `echo=False`로 변경.

---

### 3-3. `schemas/schema.py`가 서울 4개 구만 하드코딩

- **파일**: `schemas/schema.py`
- **문제**: 종로구, 중구, 용산구, 성동구만 정의. 범용적으로 사용 불가능한 불완전한 스키마.
- **수정 방향**: 삭제하거나 동적으로 처리.

---

### 3-4. 미사용 파일 / 데드 코드

| 파일 | 상태 |
|------|------|
| `core/api_connetction.py` | 어디서도 import되지 않음. 존재하지 않는 경로 `./env/.env` 참조 |
| `router/test_router.py` | 빈 파일. 등록되지 않음 |
| `utils/__init__.py` | 빈 모듈. 유틸 함수 없음 |
| `schemas/schema.py` | 불완전한 스키마. 사용되지 않음 |

---

## 4. 오타 / 네이밍

| 위치 | 현재 | 올바른 값 |
|------|------|-----------|
| `.env.exmaple` (파일명) | `exmaple` | `example` |
| `core/api_connetction.py` (파일명) | `connetction` | `connection` |
| `config.py:29` 환경변수 키 | `GOOGLE_SECRET` | `GOOGLE_CLIENT_SECRET` (변수명과 통일) |
| `.env.example:7` 키 이름 | `SSL_CA_PATH` | `DB_SSL_CA_PATH` (config.py와 통일) |

---

## 5. 우선순위 요약

| 우선순위 | 문제 | 파일 |
|---------|------|------|
| **CRITICAL** | Admin API에 인증 없음 | `admin_router.py` |
| **CRITICAL** | Report CRUD에 인증 없음 | `report_router.py` |
| **CRITICAL** | Session 시크릿키 하드코딩 | `run.py:13` |
| **HIGH** | `password_hash=None` (NOT NULL 위반) | `auth_service.py:97` |
| **HIGH** | `CrimeTypeSimple.minor`가 Optional 아님 | `schemas/report.py:22` |
| **HIGH** | `get_report` null 처리 누락 | `report_router.py:58-63` |
| **MEDIUM** | 라우터 경로 중복 | `run.py` + `official_router.py` |
| **MEDIUM** | Pydantic 모델 직접 수정 | `report_router.py:83` |
| **MEDIUM** | `echo=True` 프로덕션 노출 | `database.py:26` |
| **LOW** | 파일명/변수명 오타 | 여러 곳 |
| **LOW** | 미사용 파일/데드 코드 | `api_connetction.py` 등 |
