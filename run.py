from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from core.config import settings
from core.database import Base, engine

# 2. 라우터 임포트
from router.official_router import router as official_router
from router.admin_router import router as admin_router
from router.auth_router import router as auth_router

# 3. 애플리케이션 시작 시 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Report Management System API")

app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

app.include_router(official_router, prefix="/api/stats", tags=["Stats"])

@app.get("/")
def root():
    return {"message": "API Server is running"}

if __name__ == "__main__":
    # 서버 실행: uvicorn run:app --reload 와 동일한 효과
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)