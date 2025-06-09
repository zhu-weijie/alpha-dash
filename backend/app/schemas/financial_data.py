# app/schemas/financial_data.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class AssetCurrentPrice(BaseModel):
    symbol: str
    price: float
    last_updated: datetime


class HistoricalPricePoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    sma20: Optional[float] = None  # Add SMA fields
    sma50: Optional[float] = None
