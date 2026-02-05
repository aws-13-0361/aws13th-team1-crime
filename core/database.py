from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings # 설정 불러오기

# 설정 파일에서 조합된 URL
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={
        "ssl": {
            "fake_config": True
        }
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()