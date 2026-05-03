from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # 'admin' | 'user'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
