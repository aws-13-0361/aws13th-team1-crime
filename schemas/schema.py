from pydantic import BaseModel, Field
from typing import List
from pydantic import BaseModel
from typing import Optional

class CrimeStat(BaseModel):
    # Field의 alias를 사용해 한글 키와 매핑합니다.
    category_large: str = Field(..., alias="범죄대분류")
    category_medium: str = Field(..., alias="범죄중분류")

    # 지역별 수치 (데이터 타입은 상황에 따라 int 또는 str)
    jongno: int = Field(0, alias="서울 종로구")
    junggu: int = Field(0, alias="서울 중구")
    yongsan: int = Field(0, alias="서울 용산구")
    seongdong: int = Field(0, alias="서울 성동구")

    class Config:
        # 응답 시 영문 필드명으로 내보내고 싶을 때 설정
        populate_by_name = True
        # 공공데이터에 공백이 있을 수 있으니 유연하게 처리
        str_strip_whitespace = True


class CrimeTypeOut(BaseModel):
    id: int
    major: str
    minor: Optional[str] = None

    class Config:
        from_attributes = True  # SQLAlchemy