from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1.router import router as api_router
from app.api.v1.endpoints.auth import router as auth_router
import app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    yield


def _seed_admin():
    from app.models.user import User
    from app.core.auth import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).first():
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title="投資資產管理系統 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
