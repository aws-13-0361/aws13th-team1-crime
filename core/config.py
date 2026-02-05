import os
import secrets
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
    DB_SSL_CA_PATH = os.getenv("DB_SSL_CA_PATH")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # SQLAlchemy URL 구성
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # Session
    SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_hex(32))

    # Frontend URL (for redirect after login)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


settings = Settings()