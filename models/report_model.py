from sqlalchemy import Column, BigInteger, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from core.db_connection import Base

# 검수 상태를 위한 Enum 정의
class ReportStatus(str, enum.Enum):
    pending = "pending"  # 검수 대기
    approved = "approved"  # 승인됨
    rejected = "rejected"  # 반려됨

class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, index=True, comment="제보 ID")

    # 외래키 설정
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, comment="작성자 ID")
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False, comment="지역 ID")
    crime_type_id = Column(Integer, ForeignKey("crime_types.id"), nullable=False, comment="범죄유형 ID")

    title = Column(String(255), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    status = Column(Enum(ReportStatus), default=ReportStatus.pending, comment="검수상태")

    # 일시 관련 필드
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="작성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="승인일시")
    rejected_at = Column(DateTime(timezone=True), nullable=True, comment="반려일시")

    # 관계 설정 (필요 시 조인해서 데이터를 가져오기 위함)
    user = relationship("User", back_populates="reports")
    region = relationship("Region")
    crime_type = relationship("CrimeType")