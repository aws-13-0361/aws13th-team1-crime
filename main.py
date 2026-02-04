from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import report_router
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

@app.get("/")
async def read_root():
    return {"root": "루트입니다"}
