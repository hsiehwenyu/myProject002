from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from .endpoints import portfolios, securities, stocks, users, menu_items

router = APIRouter(dependencies=[Depends(get_current_user)])

router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
router.include_router(securities.router, tags=["securities"])
router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(menu_items.router, prefix="/menu-items", tags=["menu-items"])
