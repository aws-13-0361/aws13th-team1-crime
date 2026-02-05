from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from schemas.auth import UserResponse
from services.auth_service import (
    create_or_update_google_user,
    exchange_code_for_token,
    get_google_login_url,
    get_google_user_info,
    get_user_by_id,
)

router = APIRouter(prefix="/api", tags=["Auth"])

def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_user_by_id(db, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/auth/google/login")
def google_login():
    login_url = get_google_login_url()
    return RedirectResponse(url=login_url)


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db),
):
    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        google_user = await get_google_user_info(access_token)
        user = create_or_update_google_user(db, google_user)

        request.session["user_id"] = user.id

        return RedirectResponse(url=settings.FRONTEND_URL)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}
