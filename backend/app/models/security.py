from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# 預設證交稅率 (依資產類別)
ASSET_TYPE_TAX_RATES = {
    "股票-個股": "0.003",
    "股票ETF": "0.001",
    "債券-ETF": "0.000",
    "CB": "0.001",
    "CBAS": "0.001",
}

DEFAULT_FEE_RATE = "0.001425"


class Security(Base):
    __tablename__ = "securities"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    sec_id = Column(String(20), nullable=False)
    sec_name = Column(String(100), nullable=False)
    curr_price = Column(Numeric(14, 4), nullable=True)
    asset_type = Column(String(20), nullable=False)
    shares = Column(Integer, nullable=False, default=0)
    fee_rate = Column(Numeric(8, 6), nullable=False, default=DEFAULT_FEE_RATE)
    tax_rate = Column(Numeric(8, 6), nullable=False, default="0.003")
    price_unavailable = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    portfolio = relationship("Portfolio", back_populates="securities")
