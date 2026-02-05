import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # DB 접속 정보
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME")

    # SSL 인증서 경로 추가 (기본값 설정)
    DB_SSL_CA_PATH = os.getenv("DB_SSL_CA_PATH", "./certs/global-bundle.pem")

    # SQLAlchemy URL 구성
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

settings = Settings()