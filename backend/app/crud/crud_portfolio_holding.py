# app/crud/crud_portfolio_holding.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app import models, schemas

def create_portfolio_holding(
    db: Session, *, holding_in: schemas.PortfolioHoldingCreate, user_id: int
) -> models.PortfolioHolding:
    db_holding = models.PortfolioHolding(
        **holding_in.model_dump(), # Pydantic V2, was .dict()
        user_id=user_id
    )
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding

def get_portfolio_holdings_by_user(
    db: Session, *, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.PortfolioHolding]:
    return (
        db.query(models.PortfolioHolding)
        .filter(models.PortfolioHolding.user_id == user_id)
        .options(joinedload(models.PortfolioHolding.asset_info)) # Eager load asset info
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_portfolio_holding(
    db: Session, *, holding_id: int, user_id: int # Ensure user owns it
) -> Optional[models.PortfolioHolding]:
    return (
        db.query(models.PortfolioHolding)
        .filter(models.PortfolioHolding.id == holding_id, models.PortfolioHolding.user_id == user_id)
        .options(joinedload(models.PortfolioHolding.asset_info)) # Eager load asset info
        .first()
    )

# Add update and delete for holdings later
# def update_portfolio_holding(...)
# def remove_portfolio_holding(...)
