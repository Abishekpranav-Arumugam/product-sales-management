from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth_schema import (
    AuthResponse,
    TokenResponse,
    UserAuthResponse,
    UserLogin,
    UserRegister)
from app.security.dependencies import get_current_user
from app.service.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse)
def register_user(payload: UserRegister) -> dict[str, Any]:
    try:
        user = auth_service.create_user(
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)) from exc

    token = auth_service.create_token_for_user(
        user.id, user.email, user.role
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLogin) -> dict[str, Any]:
    user = auth_service.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth_service.create_token_for_user(
        user.id, user.email, user.role
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserAuthResponse)
def get_me(current_user: Any = Depends(get_current_user)) -> Any:
    return current_user


@router.post("/token", response_model=TokenResponse)
def create_token(payload: UserLogin) -> dict[str, str]:
    user = auth_service.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = auth_service.create_token_for_user(
        user.id, user.email, user.role
    )
    return {"access_token": token, "token_type": "bearer"}
