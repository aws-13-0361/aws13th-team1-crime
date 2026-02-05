from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import report_router, official_stats_endpoint
from utils.database import get_db
from models import User, Region, CrimeType, Report
import uvicorn
from router.admin_router import router as admin_router

app = FastAPI()

origins = [
    "http://localhost:5173" # Vite 기본 포트
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모두 허용
    allow_headers=["*"],
)
app.include_router(report_router.router)

app.include_router(official_stats_endpoint.router)

app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

@app.get("/", tags=["Default"])
async def read_root():
    return {"root": "루트입니다"}

@app.get("/api/regions", tags=["Default"])
def get_regions(db: Session = Depends(get_db)):
    return db.query(Region).all()

@app.get("/api/crime-types", tags=["Default"])
def get_crime_types(db: Session = Depends(get_db)):
    return db.query(CrimeType).all()

@app.get("/")
def root():
    return {"message": "API Server is running"}

if __name__ == "__main__":
    # 서버 실행: uvicorn run:app --reload 와 동일한 효과
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)