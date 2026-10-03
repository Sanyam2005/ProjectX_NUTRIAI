from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    mode: Literal["microsoft", "guest", "password", "signup"] = "guest"
    # For mock Microsoft sign-in: provide an id_token in real Entra ID flows.
    id_token: str | None = None
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    avatar_url: str | None = None
    is_guest: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
