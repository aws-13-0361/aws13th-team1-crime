# AI 범죄유형 자동분류 구현 가이드

## 개요
제보 작성 시 OpenAI API로 `content`를 분석하여 **crime_type_id를 자동 덮어쓰기**한다.
- Model, Schema, DB 변경 **없음**
- 프론트엔드 변경 **없음**
- AI 실패 시 프론트가 보낸 원래 값 그대로 저장 (서비스 중단 없음)

---

## 수정할 파일 목록 (5개)

| # | 파일 | 작업 |
|---|------|------|
| 1 | `requirements.txt` | 수정 - openai 패키지 추가 |
| 2 | `.env` | 수정 - API 키 추가 |
| 3 | `core/config.py` | 수정 - 환경변수 1줄 추가 |
| 4 | `services/ai_crime_classifier.py` | **새 파일** - AI 분류 서비스 |
| 5 | `router/report_router.py` | 수정 - create_report에 AI 호출 추가 |

**변경 없는 파일**: `models/report.py`, `schemas/report.py`, `admin_router.py`, `report_service.py`, MySQL DB

---

## Step 1: requirements.txt

```diff
 DBUtils==3.1.2

+# AI
+openai==1.82.0
+
 # Utilities
 filelock==3.20.3
```

```bash
pip install -r requirements.txt
```

---

## Step 2: .env

맨 아래에 추가:

```diff
 DB_SSL_CA_PATH=./certs/global-bundle.pem
+
+OPENAI_API_KEY=sk-실제키를여기에입력
```

---

## Step 3: core/config.py

`Settings` 클래스에 1줄 추가:

```diff
     DB_SSL_CA_PATH = os.getenv("DB_SSL_CA_PATH")

+    # OpenAI
+    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
+
     # SQLAlchemy URL 구성
```

---

## Step 4: services/ai_crime_classifier.py (새 파일)

```python
import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from core.config import settings
from models.crime_type import CrimeType

logger = logging.getLogger(__name__)


def classify_crime_type(db: Session, content: str) -> int | None:
    """
    제보 content를 AI가 분석하여 가장 적합한 crime_type_id를 반환한다.
    실패 시 None을 반환한다.
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY가 설정되지 않아 AI 분류를 건너뜁니다.")
        return None

    crime_types = db.query(CrimeType).all()
    if not crime_types:
        logger.warning("crime_types 테이블이 비어있어 AI 분류를 건너뜁니다.")
        return None

    crime_list = json.dumps(
        [{"id": ct.id, "major": ct.major, "minor": ct.minor} for ct in crime_types],
        ensure_ascii=False
    )

    prompt = f"""아래는 범죄 제보 내용입니다. 가장 적합한 범죄 유형의 id를 골라주세요.

## 범죄 유형 목록
{crime_list}

## 제보 내용
{content}

## 규칙
- 반드시 위 목록에 있는 id 중 하나만 숫자로 응답하세요.
- 다른 텍스트 없이 숫자만 응답하세요.
- 판단이 어려우면 가장 가까운 유형의 id를 선택하세요.
"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 범죄 유형 분류 전문가야. 숫자만 응답해."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0
        )

        ai_answer = response.choices[0].message.content.strip()
        crime_type_id = int(ai_answer)

        valid_ids = {ct.id for ct in crime_types}
        if crime_type_id not in valid_ids:
            logger.warning(f"AI가 반환한 ID({crime_type_id})가 유효하지 않습니다.")
            return None

        return crime_type_id

    except Exception as e:
        logger.error(f"AI 범죄유형 분류 중 오류 발생: {e}")
        return None
```

---

## Step 5: router/report_router.py

### 5-1. import 추가 (파일 상단)

```diff
 from sqlalchemy import desc, or_
+from services.ai_crime_classifier import classify_crime_type
```

### 5-2. create_report 함수 수정

**변경 전:**
```python
@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
        report_data: ReportCreate,
        db: Session = Depends(get_db)
):
    new_report = Report(**report_data.model_dump())
    try:
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return new_report
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제보 저장 중 오류가 발생했습니다: {str(e)}"
        )
```

**변경 후:**
```python
@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
        report_data: ReportCreate,
        db: Session = Depends(get_db)
):
    # AI가 content를 분석하여 crime_type_id 덮어쓰기
    ai_crime_type_id = classify_crime_type(db, report_data.content)
    if ai_crime_type_id is not None:
        report_data.crime_type_id = ai_crime_type_id

    new_report = Report(**report_data.model_dump())
    try:
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return new_report
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제보 저장 중 오류가 발생했습니다: {str(e)}"
        )
```

**변경점은 3줄뿐:**
```python
ai_crime_type_id = classify_crime_type(db, report_data.content)
if ai_crime_type_id is not None:
    report_data.crime_type_id = ai_crime_type_id
```

> dict 변환 불필요. `crime_type_id`는 `ReportCreate`에 이미 있는 필드라서 직접 덮어쓰기 가능.

---

## 전체 동작 흐름

```
프론트 → POST /api/reports { crime_type_id: 5, content: "어젯밤 강도..." }
  ↓
서버: AI에게 content 전달
  ↓
AI 응답: "2" (강력범죄 > 강도)
  ↓
report_data.crime_type_id = 5 → 2 덮어쓰기
  ↓
Report 저장 (crime_type_id = 2)
  ↓
응답: { crime_type: { id: 2, major: "강력범죄", minor: "강도" }, ... }
```

---

## 안전장치

| 상황 | 동작 |
|------|------|
| AI 성공 | `crime_type_id`를 AI 결과로 덮어쓰기 |
| API 키 없음 | AI 스킵, 프론트 값 그대로 저장 |
| AI 오류/타임아웃 | AI 스킵, 프론트 값 그대로 저장 |
| AI가 잘못된 id 반환 | AI 스킵, 프론트 값 그대로 저장 |

---

## 검증 방법

1. **Swagger** `POST /api/reports` → `crime_type_id: 99`로 보내도 AI가 올바른 값으로 변경되는지 확인
2. **`.env`에서 `OPENAI_API_KEY` 제거** 후 테스트 → 프론트 값(99) 그대로 저장 확인
3. **`POST /api/admin/reports/{id}/approve`** → 올바른 `crime_type_id`로 통계 증가 확인

---

## 작업 체크리스트

```
[ ] 1. requirements.txt에 openai 추가 + pip install
[ ] 2. .env에 OPENAI_API_KEY 추가
[ ] 3. core/config.py에 OPENAI_API_KEY 1줄 추가
[ ] 4. services/ai_crime_classifier.py 새로 생성
[ ] 5. router/report_router.py에 import 1줄 + 로직 3줄 추가
[ ] 6. 서버 재시작 후 Swagger 테스트
```
