from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models.user import UserRole


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    role: UserRole
    auth_provider: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoogleUserInfo(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
