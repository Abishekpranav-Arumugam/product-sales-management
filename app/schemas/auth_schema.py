import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["user", "supervisor"] = "user"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one numeric character")
        if not re.search(r"[@_#]", value):
            raise ValueError("Password must contain at least one of these special characters: @, _, #")
        if not re.fullmatch(r"[A-Za-z0-9@_#]+", value):
            raise ValueError("Password contains invalid characters. Only letters, numbers, @, _, and # are allowed")
        return value


class UserLogin(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one numeric character")
        if not re.search(r"[@_#]", value):
            raise ValueError("Password must contain at least one of these special characters: @, _, #")
        if not re.fullmatch(r"[A-Za-z0-9@_#]+", value):
            raise ValueError("Password contains invalid characters. Only letters, numbers, @, _, and # are allowed")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserAuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Literal["user", "supervisor"]


class AuthResponse(BaseModel):
    user: UserAuthResponse
    access_token: str
    token_type: str = "bearer"
