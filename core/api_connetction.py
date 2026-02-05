import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
dotenv_db_path = BASE_DIR / "./env/.env"

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

