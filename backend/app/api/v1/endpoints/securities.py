from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.security import Security, ASSET_TYPE_TAX_RATES
from app.schemas.security import (
    SecurityCreate, SecurityUpdate, SecurityPriceUpdate, SecurityResponse
)

router = APIRouter()


@router.get("/portfolios/{portfolio_id}/securities", response_model=List[SecurityResponse])
def list_securities(portfolio_id: int, db: Session = Depends(get_db)):
    if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
        raise HTTPException(status_code=404, detail="Portfolio not found")
    securities = db.query(Security).filter(Security.portfolio_id == portfolio_id).all()
    return [SecurityResponse.from_orm_with_calc(s) for s in securities]


@router.post("/portfolios/{portfolio_id}/securities", response_model=SecurityResponse, status_code=201)
def create_security(portfolio_id: int, payload: SecurityCreate, db: Session = Depends(get_db)):
    if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
        raise HTTPException(status_code=404, detail="Portfolio not found")
    security = Security(portfolio_id=portfolio_id, **payload.model_dump())
    db.add(security)
    db.commit()
    db.refresh(security)
    return SecurityResponse.from_orm_with_calc(security)


@router.get("/securities/{security_id}", response_model=SecurityResponse)
def get_security(security_id: int, db: Session = Depends(get_db)):
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    return SecurityResponse.from_orm_with_calc(security)


@router.put("/securities/{security_id}", response_model=SecurityResponse)
def update_security(security_id: int, payload: SecurityUpdate, db: Session = Depends(get_db)):
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    updates = payload.model_dump(exclude_none=True)
    # Auto-update tax_rate when asset_type changes (unless tax_rate is explicitly provided)
    if "asset_type" in updates and "tax_rate" not in updates:
        updates["tax_rate"] = ASSET_TYPE_TAX_RATES.get(updates["asset_type"], "0.003")
    for field, value in updates.items():
        setattr(security, field, value)
    db.commit()
    db.refresh(security)
    return SecurityResponse.from_orm_with_calc(security)


@router.patch("/securities/{security_id}/price", response_model=SecurityResponse)
def update_price(security_id: int, payload: SecurityPriceUpdate, db: Session = Depends(get_db)):
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    security.curr_price = payload.curr_price
    security.price_unavailable = payload.price_unavailable
    db.commit()
    db.refresh(security)
    return SecurityResponse.from_orm_with_calc(security)


@router.delete("/securities/{security_id}", status_code=204)
def delete_security(security_id: int, db: Session = Depends(get_db)):
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(status_code=404, detail="Security not found")
    db.delete(security)
    db.commit()


@router.get("/asset-types")
def list_asset_types():
    return [
        {"asset_type": k, "default_tax_rate": v}
        for k, v in ASSET_TYPE_TAX_RATES.items()
    ]
