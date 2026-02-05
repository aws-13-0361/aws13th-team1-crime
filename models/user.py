import enum
from sqlalchemy import Column, BigInteger, String, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, comment="사용자 ID")
    email = Column(String(255), unique=True, nullable=False, comment="이메일")
    password_hash = Column(String(255), nullable=False, comment="비밀번호")
    role = Column(
        Enum(UserRole, native_enum=False),
        default=UserRole.user,
        nullable=False,
        comment="user/admin"
    )

    nickname = Column(String(50), comment="닉네임")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="가입일시")
    google_id  = Column(String(255), nullable=False, comment="구글 아이디 ")
    auth_provider  = Column(String(255), nullable=False, comment="auth_provider ")
    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', nickname='{self.nickname}')>"
