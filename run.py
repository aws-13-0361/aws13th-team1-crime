from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from core.database import get_db
from models import Region, CrimeType
from router import report_router, official_router, auth_router
from router.admin_router import router as admin_router

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="your-very-secret-key-here",
    same_site="lax",
    https_only=False
    # 세션 암호화 키 (임의 설정)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE 등 모두 허용
    allow_headers=["*"],
)
app.include_router(report_router.router)

app.include_router(official_router.router)

app.include_router(auth_router.router)

app.include_router(admin_router)

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

