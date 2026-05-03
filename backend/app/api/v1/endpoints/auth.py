from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.auth import create_token, authenticate_user, get_current_user, CurrentUser
from app.core.database import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(payload.username, payload.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    return TokenResponse(
        access_token=create_token(user.username, user.role),
        username=user.username,
        role=user.role,
    )


@router.get("/me")
def me(current: CurrentUser = Depends(get_current_user)):
    return {"username": current.username, "role": current.role}
