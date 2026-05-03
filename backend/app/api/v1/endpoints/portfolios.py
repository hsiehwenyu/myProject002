from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List
from collections import defaultdict

from app.core.database import get_db
from app.models.portfolio import Portfolio
from app.models.security import Security
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioSummaryResponse, AssetTypeSummary,
)
from app.schemas.security import SecurityCreate, SecurityResponse

router = APIRouter()


@router.get("/", response_model=List[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db)):
    return db.query(Portfolio).order_by(Portfolio.created_at.desc()).all()


@router.post("/", response_model=PortfolioResponse, status_code=201)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)):
    portfolio = Portfolio(**payload.model_dump())
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioSummaryResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    securities_resp = [SecurityResponse.from_orm_with_calc(s) for s in portfolio.securities]

    totals = {
        "mv_1": Decimal("0"), "tx_fee": Decimal("0"),
        "tx_tax": Decimal("0"), "mv_2": Decimal("0"),
    }
    by_type: dict = defaultdict(lambda: {"count": 0, "mv_1": Decimal("0"), "tx_fee": Decimal("0"), "tx_tax": Decimal("0"), "mv_2": Decimal("0")})

    for s in securities_resp:
        totals["mv_1"] += s.mv_1
        totals["tx_fee"] += s.tx_fee
        totals["tx_tax"] += s.tx_tax
        totals["mv_2"] += s.mv_2
        g = by_type[s.asset_type]
        g["count"] += 1
        g["mv_1"] += s.mv_1
        g["tx_fee"] += s.tx_fee
        g["tx_tax"] += s.tx_tax
        g["mv_2"] += s.mv_2

    by_asset_type = [
        AssetTypeSummary(asset_type=k, **v) for k, v in by_type.items()
    ]

    return PortfolioSummaryResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        securities=securities_resp,
        totals=totals,
        by_asset_type=by_asset_type,
    )


@router.post("/{portfolio_id}/import", response_model=List[SecurityResponse], status_code=201)
def import_securities(portfolio_id: int, rows: List[SecurityCreate], db: Session = Depends(get_db)):
    if not db.query(Portfolio).filter(Portfolio.id == portfolio_id).first():
        raise HTTPException(status_code=404, detail="Portfolio not found")
    created = []
    for row in rows:
        s = Security(portfolio_id=portfolio_id, **row.model_dump())
        db.add(s)
        created.append(s)
    db.commit()
    for s in created:
        db.refresh(s)
    return [SecurityResponse.from_orm_with_calc(s) for s in created]


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(portfolio, field, value)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
