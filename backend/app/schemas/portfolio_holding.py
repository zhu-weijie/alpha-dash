# app/schemas/portfolio_holding.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .asset import Asset


class PortfolioHoldingBase(BaseModel):
    asset_id: int
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., ge=0)
    purchase_date: datetime


class PortfolioHoldingCreate(PortfolioHoldingBase):
    pass


class PortfolioHolding(PortfolioHoldingBase):
    id: int
    user_id: int
    created_at: datetime
    asset_info: Optional[Asset] = None

    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None

    model_config = {"from_attributes": True}


class PortfolioHoldingSimple(PortfolioHoldingBase):
    id: int
    user_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class PortfolioHoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, ge=0)
    purchase_date: Optional[datetime] = None
