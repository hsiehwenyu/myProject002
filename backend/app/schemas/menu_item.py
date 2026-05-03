from pydantic import BaseModel
from typing import Optional


class MenuItemCreate(BaseModel):
    label: str
    url: str
    icon: str = "🔗"
    sort_order: int = 0
    is_active: bool = True
    min_role: str = "user"


class MenuItemUpdate(BaseModel):
    label: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    min_role: Optional[str] = None


class MenuItemRead(BaseModel):
    id: int
    label: str
    url: str
    icon: str
    sort_order: int
    is_active: bool
    min_role: str

    model_config = {"from_attributes": True}
