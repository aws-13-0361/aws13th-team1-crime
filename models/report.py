from sqlalchemy import Column, BigInteger, Integer, String, Text, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
import enum
from core.database import Base

class ReportStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    crime_type_id = Column(Integer, ForeignKey("crime_types.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # default 값도 소문자 멤버인 ReportStatus.pending으로 변경
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.pending)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=True)
    approved_at = Column(TIMESTAMP, nullable=True)
    rejected_at = Column(TIMESTAMP, nullable=True)