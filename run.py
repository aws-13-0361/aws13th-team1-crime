from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

# 1. 라우터 및 필요한 모듈 임포트
from router import report_router, official_router
from router.admin_router import router as admin_router
from core.database import get_db, engine, Base
from models import Region, CrimeType
import models  # 테이블 자동 생성을 위해 모든 모델 로드

# 2. 데이터베이스 테이블 생성
# run.py 실행 시점에 DB에 테이블이 없다면 자동으로 생성합니다.
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Safety Report API",
    description="제보 관리 및 통계 조회를 위한 백엔드 서버",
    version="1.0.0"
)

# 3. CORS 설정
origins = [
    "http://localhost:5173", # Vite(Frontend) 기본 포트
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 라우터 등록 (중복 제거 및 구조화)
# 제보 관련 라우터
app.include_router(report_router.router, prefix="/api/reports", tags=["Reports"])

# 통계 관련 라우터
app.include_router(official_router.router, prefix="/api/stats", tags=["Stats"])

# 관리자 전용 라우터
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


# 5. 공통 엔드포인트
@app.get("/", tags=["Default"])
async def root():
    """서버 상태 확인용 루트 엔드포인트"""
    return {"message": "Safety Report API Server is running", "status": "online"}

@app.get("/api/regions", tags=["Default"])
def get_regions(db: Session = Depends(get_db)):
    """지역 목록 조회"""
    return db.query(Region).all()

@app.get("/api/crime-types", tags=["Default"])
def get_crime_types(db: Session = Depends(get_db)):
    """범죄 유형 목록 조회"""
    return db.query(CrimeType).all()