from pydantic import BaseModel, model_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.models.security import ASSET_TYPE_TAX_RATES, DEFAULT_FEE_RATE

ASSET_TYPES = list(ASSET_TYPE_TAX_RATES.keys())


def _calc_fields(price, shares, fee_rate, tax_rate, unavailable):
    if unavailable or price is None:
        mv1 = Decimal("0")
    else:
        mv1 = Decimal(str(price)) * Decimal(str(shares))
    tx_fee = round(mv1 * Decimal(str(fee_rate)), 0)
    tx_tax = round(mv1 * Decimal(str(tax_rate)), 0)
    mv2 = mv1 - tx_fee - tx_tax
    return mv1, tx_fee, tx_tax, mv2


class SecurityCreate(BaseModel):
    sec_id: str
    sec_name: str
    curr_price: Optional[Decimal] = None
    asset_type: str
    shares: int
    fee_rate: Optional[Decimal] = Decimal(DEFAULT_FEE_RATE)
    tax_rate: Optional[Decimal] = None
    price_unavailable: bool = False

    @model_validator(mode="after")
    def set_tax_rate_default(self):
        if self.tax_rate is None:
            rate = ASSET_TYPE_TAX_RATES.get(self.asset_type, "0.003")
            self.tax_rate = Decimal(rate)
        return self


class SecurityUpdate(BaseModel):
    sec_id: Optional[str] = None
    sec_name: Optional[str] = None
    curr_price: Optional[Decimal] = None
    asset_type: Optional[str] = None
    shares: Optional[int] = None
    fee_rate: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    price_unavailable: Optional[bool] = None


class SecurityPriceUpdate(BaseModel):
    curr_price: Optional[Decimal] = None
    price_unavailable: bool = False


class SecurityResponse(BaseModel):
    id: int
    portfolio_id: int
    sec_id: str
    sec_name: str
    curr_price: Optional[Decimal]
    asset_type: str
    shares: int
    fee_rate: Decimal
    tax_rate: Decimal
    price_unavailable: bool
    mv_1: Decimal
    tx_fee: Decimal
    tx_tax: Decimal
    mv_2: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_calc(cls, obj):
        mv1, tx_fee, tx_tax, mv2 = _calc_fields(
            obj.curr_price, obj.shares, obj.fee_rate, obj.tax_rate, obj.price_unavailable
        )
        return cls(
            id=obj.id,
            portfolio_id=obj.portfolio_id,
            sec_id=obj.sec_id,
            sec_name=obj.sec_name,
            curr_price=obj.curr_price,
            asset_type=obj.asset_type,
            shares=obj.shares,
            fee_rate=obj.fee_rate,
            tax_rate=obj.tax_rate,
            price_unavailable=obj.price_unavailable,
            mv_1=mv1,
            tx_fee=tx_fee,
            tx_tax=tx_tax,
            mv_2=mv2,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
