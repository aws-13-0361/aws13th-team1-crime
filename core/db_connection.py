from sqlalchemy import create_engine
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent
dotenv_db_path = BASE_DIR / "./env/.env_DB"

# verbose=True를 넣으면 로드 과정을 상세히 출력해줍니다.
if load_dotenv(dotenv_path=dotenv_db_path, verbose=True):
    print(f"✅ .env_DB 로드 성공! (경로: {dotenv_db_path})")
else:
    print(f"❌ .env_DB 로드 실패! (파일이 해당 경로에 있는지 확인하세요: {dotenv_db_path})")
def get_env(key:str, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"환경변수 누락 : {key}")
    return value

db_config={
"user" : get_env("DB_USER"),
"password" : get_env("DB_PASSWORD"),
"host" : get_env("DB_HOST"),
"db_name" : get_env("DB_NAME"),
"port" : int(get_env("DB_PORT")),
"ssl_args" : get_env("SSL_ARGS_PATH")
}

print(db_config["ssl_args"])

SSL_ARGS = {'ssl': {'ca': rf'{db_config["ssl_args"]}'}}
db_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
# 데이터베이스 엔진 생성
engine = create_engine(
    db_url,
    connect_args=SSL_ARGS,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

print("✅ 모든 정규화 테이블에 데이터 업로드가 완료되었습니다!")