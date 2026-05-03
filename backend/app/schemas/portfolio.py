from pydantic import BaseModel
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime
from .security import SecurityResponse


class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetTypeSummary(BaseModel):
    asset_type: str
    count: int
    mv_1: Decimal
    tx_fee: Decimal
    tx_tax: Decimal
    mv_2: Decimal


class PortfolioSummaryResponse(PortfolioResponse):
    securities: List[SecurityResponse]
    totals: Dict[str, Decimal]
    by_asset_type: List[AssetTypeSummary]
