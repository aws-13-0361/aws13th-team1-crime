from fastapi import FastAPI
import uvicorn

# 1. 모델 및 데이터베이스 설정 임포트
# models/__init__.py를 만드셨다면 아래 한 줄로 요약 가능합니다.
from core.database import Base, engine

# 2. 라우터 임포트
from router.admin_router import router as admin_router

# 3. 애플리케이션 시작 시 테이블 생성
# (이미 존재하면 무시되고, 없는 테이블만 생성됩니다.)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Report Management System API")

# 4. 관리자 라우터 등록
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "API Server is running"}

if __name__ == "__main__":
    # 서버 실행: uvicorn run:app --reload 와 동일한 효과
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)