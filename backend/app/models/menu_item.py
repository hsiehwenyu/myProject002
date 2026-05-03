from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    icon = Column(String(10), nullable=False, default="🔗")
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    min_role = Column(String(20), nullable=False, default="user")  # 'user' | 'admin'
