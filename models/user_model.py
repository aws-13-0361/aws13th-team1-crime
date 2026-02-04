import enum
from sqlalchemy import Column, BigInteger, String, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db_connection import Base


# 1. str을 상속받는 Enum 클래스 정의
# 이렇게 하면 "user"라는 문자열과 UserRole.USER를 동일하게 취급하기 쉬워집니다.
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    # ERD 기준 컬럼 정의
    id = Column(BigInteger, primary_key=True, index=True, comment="사용자 ID")
    email = Column(String(255), unique=True, nullable=False, comment="이메일")
    password_hash = Column(String(255), nullable=False, comment="비밀번호")

    # 2. Enum 설정 수정
    # native_enum=False를 주면 DB에 제약 조건 대신 단순 문자열로 저장되어
    # 대소문자나 값 매핑 에러를 방지하는 데 유리합니다.
    role = Column(
        Enum(UserRole, native_enum=False),
        default=UserRole.user,
        nullable=False,
        comment="user/admin"
    )

    nickname = Column(String(50), comment="닉네임")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="가입일시")

    # 3. 관계 설정 (Report 모델과의 연결)
    # Report 모델에서 user = relationship("User", back_populates="reports")로 정의했다면
    # 여기서도 대칭을 맞춰줘야 합니다.
    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', nickname='{self.nickname}')>"