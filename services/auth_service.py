from typing import Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from core.config import settings
from models.user import User
from schemas.auth import GoogleUserInfo


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_login_url() -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_google_user_info(access_token: str) -> GoogleUserInfo:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()
        return GoogleUserInfo(
            id=data["id"],
            email=data["email"],
            name=data.get("name", data["email"].split("@")[0]),
            picture=data.get("picture"),
        )


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    return db.query(User).filter(User.google_id == google_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_or_update_google_user(db: Session, google_user: GoogleUserInfo) -> User:
    user = get_user_by_google_id(db, google_user.id)

    if user:
        user.email = google_user.email
        user.nickname = google_user.name
        db.commit()
        db.refresh(user)
        return user

    existing_email_user = get_user_by_email(db, google_user.email)
    if existing_email_user:
        existing_email_user.google_id = google_user.id
        existing_email_user.auth_provider = "google"
        existing_email_user.nickname = google_user.name
        db.commit()
        db.refresh(existing_email_user)
        return existing_email_user

    new_user = User(
        email=google_user.email,
        nickname=google_user.name,
        google_id=google_user.id,
        auth_provider="google",
        password_hash=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
