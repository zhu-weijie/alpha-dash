# app/crud/crud_portfolio_holding.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Union, Dict, Any
from app import models, schemas
from app.crud import get_asset
from sqlalchemy import func, cast, Float


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


def get_user_aggregated_asset_summary(
    db: Session, *, user_id: int
) -> List[Dict[str, Any]]:
    """
    Gets a summary of distinct assets held by a user, with total quantity
    and weighted average purchase price for each asset.
    """
    sum_quantity = func.sum(models.PortfolioHolding.quantity)
    sum_total_cost = func.sum(
        models.PortfolioHolding.quantity * models.PortfolioHolding.purchase_price
    )

    summary_query = (
        db.query(
            models.Asset.id.label("asset_id"),
            models.Asset.symbol.label("symbol"),
            models.Asset.name.label("name"),
            models.Asset.asset_type.label("asset_type"),
            sum_quantity.label("total_quantity"),
            (
                cast(sum_total_cost, Float)
                / func.nullif(cast(sum_quantity, Float), 0.0)
            ).label("weighted_average_purchase_price"),
        )
        .join(models.Asset, models.PortfolioHolding.asset_id == models.Asset.id)
        .filter(models.PortfolioHolding.user_id == user_id)
        .group_by(
            models.Asset.id,
            models.Asset.symbol,
            models.Asset.name,
            models.Asset.asset_type,
        )
        .order_by(models.Asset.symbol)
    )

    results = summary_query.all()

    return [
        {
            "asset_id": r.asset_id,
            "symbol": r.symbol,
            "name": r.name,
            "asset_type": r.asset_type,
            "total_quantity": (
                float(r.total_quantity) if r.total_quantity is not None else 0.0
            ),
            "weighted_average_purchase_price": (
                float(r.weighted_average_purchase_price)
                if r.weighted_average_purchase_price is not None
                else 0.0
            ),
        }
        for r in results
    ]
