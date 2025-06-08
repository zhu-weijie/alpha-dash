# app/api/endpoints/market_data.py
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from app.services import get_current_price, get_historical_data
from app import schemas

router = APIRouter()

@router.get("/{symbol}/price", response_model=Optional[schemas.AssetCurrentPrice])
async def get_asset_current_price(symbol: str):
    """
    Get the current market price for a given asset symbol.
    """
    price = get_current_price(symbol)
    if price is None:
        # Decide if 404 is appropriate or if service layer should raise specific errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Could not retrieve current price for symbol {symbol}"
        )
    return schemas.AssetCurrentPrice(symbol=symbol, price=price, last_updated=datetime.now())

@router.get("/{symbol}/history", response_model=Optional[List[schemas.HistoricalPricePoint]])
async def get_asset_historical_data(
    symbol: str, 
    outputsize: str = Query("compact", enum=["compact", "full"])
):
    """
    Get historical daily price data for a given asset symbol.
    - `outputsize`: "compact" (last 100 data points) or "full" (entire history).
    """
    history = get_historical_data(symbol, outputsize=outputsize)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not retrieve historical data for symbol {symbol}"
        )
    return history
