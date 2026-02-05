from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from core.config import settings
from core.database import Base, engine

from router.admin_router import router as admin_router
from router.auth_router import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Report Management System API")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="session",
    max_age=60 * 60 * 24 * 7,  # 7 days
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
def root():
    return {"message": "API Server is running"}

if __name__ == "__main__":
    # 서버 실행: uvicorn run:app --reload 와 동일한 효과
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)