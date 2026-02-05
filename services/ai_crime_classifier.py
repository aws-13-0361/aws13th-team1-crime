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
