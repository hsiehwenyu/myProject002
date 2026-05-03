import jwt
from dataclasses import dataclass
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt as _bcrypt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

_bearer = HTTPBearer(auto_error=False)
_ALGORITHM = "HS256"
_EXPIRE_HOURS = 24


@dataclass
class CurrentUser:
    username: str
    role: str


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def _decode_token(token: str) -> CurrentUser | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "user")
        if not username:
            return None
        return CurrentUser(username=username, role=role)
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="未登入，請先登入")
    user = _decode_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="登入已逾時，請重新登入")
    return user


def get_current_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理員權限")
    return current


def authenticate_user(username: str, password: str, db: Session) -> CurrentUser | None:
    from app.models.user import User
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return CurrentUser(username=user.username, role=user.role)
