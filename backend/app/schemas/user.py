from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
