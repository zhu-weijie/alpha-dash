# app/schemas/financial_data.py
from pydantic import BaseModel
from datetime import date, datetime

class AssetCurrentPrice(BaseModel):
    symbol: str
    price: float
    last_updated: datetime # Or just the date the price was fetched

class HistoricalPricePoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
