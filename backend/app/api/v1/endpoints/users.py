from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.auth import get_current_admin, CurrentUser, hash_password
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRead

router = APIRouter()


@router.get("/", response_model=List[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    return db.query(User).order_by(User.id).all()


@router.post("/", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="帳號已存在")
    if payload.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role 必須為 admin 或 user")
    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.username == current.username and payload.role and payload.role != "admin":
        raise HTTPException(status_code=400, detail="無法降低自己的管理員權限")
    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="使用者不存在")
    if user.username == current.username:
        raise HTTPException(status_code=400, detail="無法刪除自己的帳號")
    db.delete(user)
    db.commit()
