from sqlalchemy import Column, BigInteger, String, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from core.db_connection import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    nickname = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Report와의 관계 설정
    reports = relationship("Report", back_populates="user")