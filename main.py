from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import report_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vue 개발 서버 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router.router)


@app.get("/")
async def read_root():
    return {"root": "루트입니다"}
