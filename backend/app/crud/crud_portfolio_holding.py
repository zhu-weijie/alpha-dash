# app/crud/crud_portfolio_holding.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Union, Dict, Any
from app import models, schemas
from app.crud import get_asset


def create_portfolio_holding(
    db: Session, *, holding_in: schemas.PortfolioHoldingCreate, user_id: int
) -> models.PortfolioHolding:
    db_holding = models.PortfolioHolding(**holding_in.model_dump(), user_id=user_id)
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
        .options(joinedload(models.PortfolioHolding.asset_info))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_portfolio_holding(
    db: Session, *, holding_id: int, user_id: int
) -> Optional[models.PortfolioHolding]:
    return (
        db.query(models.PortfolioHolding)
        .filter(
            models.PortfolioHolding.id == holding_id,
            models.PortfolioHolding.user_id == user_id,
        )
        .options(joinedload(models.PortfolioHolding.asset_info))
        .first()
    )


def update_portfolio_holding(
    db: Session,
    *,
    db_holding: models.PortfolioHolding,
    holding_in: Union[schemas.PortfolioHoldingUpdate, Dict[str, Any]]
) -> models.PortfolioHolding:
    if isinstance(holding_in, dict):
        update_data = holding_in
    else:
        update_data = holding_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(db_holding, field) and value is not None:
            setattr(db_holding, field, value)

    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    if not db_holding.asset_info and db_holding.asset_id:
        db_holding.asset_info = get_asset(db, asset_id=db_holding.asset_id)
    return db_holding


def remove_portfolio_holding(
    db: Session, *, holding_id: int, user_id: int
) -> Optional[models.PortfolioHolding]:
    db_holding = get_portfolio_holding(db=db, holding_id=holding_id, user_id=user_id)
    if db_holding:
        db.delete(db_holding)
        db.commit()
        return db_holding
    return None
