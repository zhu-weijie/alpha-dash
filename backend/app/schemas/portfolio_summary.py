# app/schemas/portfolio_summary.py
from pydantic import BaseModel
from typing import List
from .portfolio_holding import PortfolioHolding

class PortfolioSummary(BaseModel):
    total_purchase_value: float = 0.0
    total_current_value: float = 0.0
    total_gain_loss: float = 0.0
    total_gain_loss_percent: float = 0.0
    holdings: List[PortfolioHolding] = []
