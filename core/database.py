import os  # 파일 존재 확인을 위해 필요
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 1. SSL 설정 동적 구성
connect_args = {}

# 설정에 경로가 있고, 실제로 그 경로에 파일이 존재할 때만 SSL 적용
if settings.DB_SSL_CA_PATH and os.path.exists(settings.DB_SSL_CA_PATH):
    connect_args["ssl"] = {"ca": settings.DB_SSL_CA_PATH}
    print(f"🔒 DB SSL 설정 적용 완료: {settings.DB_SSL_CA_PATH}")
else:
    # 로컬 테스트 환경이나 인증서가 없는 경우를 위한 처리
    print("⚠️ SSL 인증서가 없거나 경로가 잘못되었습니다. 일반 연결을 시도합니다.")

# 2. 엔진 생성
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={
        "ssl": {
            "fake_config": True
        }
    },
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()