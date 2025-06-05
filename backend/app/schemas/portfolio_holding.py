# app/schemas/portfolio_holding.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .asset import Asset

# Shared properties
class PortfolioHoldingBase(BaseModel):
    asset_id: int
    quantity: float = Field(..., gt=0) # Quantity must be greater than 0
    purchase_price: float = Field(..., ge=0) # Price can be 0 or more
    purchase_date: datetime

# Properties to receive via API on creation
class PortfolioHoldingCreate(PortfolioHoldingBase):
    pass

# Properties to return to client
# This schema will include details of the asset itself for better UI display
class PortfolioHolding(PortfolioHoldingBase):
    id: int
    user_id: int
    created_at: datetime
    asset_info: Optional[Asset] = None # Nested Asset schema

    model_config = {
        "from_attributes": True
    }

# A simpler response if you don't want nested asset_info always
class PortfolioHoldingSimple(PortfolioHoldingBase):
    id: int
    user_id: int
    created_at: datetime
    model_config = {
        "from_attributes": True
    }
