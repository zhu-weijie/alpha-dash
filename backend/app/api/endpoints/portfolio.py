# app/api/endpoints/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any

from app import crud, models, schemas
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.services import get_current_price

router = APIRouter()


@router.post(
    "/holdings/",
    response_model=schemas.PortfolioHolding,
    status_code=status.HTTP_201_CREATED,
)
def add_asset_to_portfolio(
    *,
    db: Session = Depends(get_db),
    holding_in: schemas.PortfolioHoldingCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Add an asset holding to the current user's portfolio.
    """
    asset = crud.get_asset(db, asset_id=holding_in.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {holding_in.asset_id} not found.",
        )
    holding_model = crud.create_portfolio_holding(
        db=db, holding_in=holding_in, user_id=current_user.id
    )
    asset_schema = schemas.Asset.model_validate(holding_model.asset_info)
    holding_response = schemas.PortfolioHolding.model_validate(holding_model)
    holding_response.asset_info = asset_schema

    current_price = get_current_price(holding_model.asset_info.symbol)
    if current_price is not None:
        holding_response.current_price = current_price
        holding_response.current_value = holding_model.quantity * current_price
        purchase_value = holding_model.quantity * holding_model.purchase_price
        holding_response.gain_loss = holding_response.current_value - purchase_value
        if purchase_value > 0:
            holding_response.gain_loss_percent = (
                holding_response.gain_loss / purchase_value
            ) * 100

    return holding_response


@router.get("/holdings/", response_model=schemas.PortfolioSummary)
def view_user_portfolio_summary(
    db: Session = Depends(get_db),
    skip: int = Query(
        0, ge=0
    ),  # Pagination might apply to holdings list within summary
    limit: int = Query(100, ge=1, le=200),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve the current user's portfolio holdings with calculated current values and summary.
    """
    db_holdings = crud.get_portfolio_holdings_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )

    processed_holdings: List[schemas.PortfolioHolding] = []
    total_purchase_value = 0.0
    total_current_value = 0.0

    for db_holding in db_holdings:
        holding_schema = schemas.PortfolioHolding.model_validate(db_holding)

        if db_holding.asset_info:
            holding_schema.asset_info = schemas.Asset.model_validate(
                db_holding.asset_info
            )

            current_price = get_current_price(db_holding.asset_info.symbol)

            purchase_value_of_holding = db_holding.quantity * db_holding.purchase_price
            total_purchase_value += purchase_value_of_holding

            if current_price is not None:
                holding_schema.current_price = current_price
                current_value_of_holding = db_holding.quantity * current_price
                holding_schema.current_value = current_value_of_holding
                holding_schema.gain_loss = (
                    current_value_of_holding - purchase_value_of_holding
                )
                if purchase_value_of_holding > 0:
                    holding_schema.gain_loss_percent = (
                        holding_schema.gain_loss / purchase_value_of_holding
                    ) * 100
                else:
                    holding_schema.gain_loss_percent = (
                        0.0 if current_value_of_holding == 0 else None
                    )  # Handle 0 purchase price
                total_current_value += current_value_of_holding
            else:
                pass

        processed_holdings.append(holding_schema)

    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percent = 0.0
    if total_purchase_value > 0:
        total_gain_loss_percent = (total_gain_loss / total_purchase_value) * 100
    elif total_current_value > 0:
        total_gain_loss_percent = float("inf")

    return schemas.PortfolioSummary(
        total_purchase_value=round(total_purchase_value, 2),
        total_current_value=round(total_current_value, 2),
        total_gain_loss=round(total_gain_loss, 2),
        total_gain_loss_percent=(
            round(total_gain_loss_percent, 2)
            if total_gain_loss_percent != float("inf")
            else None
        ),
        holdings=processed_holdings,
    )


@router.get("/holdings/{holding_id}", response_model=schemas.PortfolioHolding)
def view_single_portfolio_holding(
    *,
    db: Session = Depends(get_db),
    holding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    db_holding = crud.get_portfolio_holding(
        db=db, holding_id=holding_id, user_id=current_user.id
    )
    if not db_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio holding not found or not owned by user.",
        )

    holding_response = schemas.PortfolioHolding.model_validate(db_holding)
    if db_holding.asset_info:
        holding_response.asset_info = schemas.Asset.model_validate(
            db_holding.asset_info
        )
        current_price = get_current_price(db_holding.asset_info.symbol)
        if current_price is not None:
            holding_response.current_price = current_price
            holding_response.current_value = db_holding.quantity * current_price
            purchase_value = db_holding.quantity * db_holding.purchase_price
            holding_response.gain_loss = holding_response.current_value - purchase_value
            if purchase_value > 0:
                holding_response.gain_loss_percent = (
                    holding_response.gain_loss / purchase_value
                ) * 100
    return holding_response


@router.put("/holdings/{holding_id}", response_model=schemas.PortfolioHolding)
def update_user_portfolio_holding(
    *,
    db: Session = Depends(get_db),
    holding_id: int,
    holding_in: schemas.PortfolioHoldingUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a specific portfolio holding for the current user.
    """
    db_holding = crud.get_portfolio_holding(
        db=db, holding_id=holding_id, user_id=current_user.id
    )
    if not db_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio holding not found or not owned by user.",
        )

    updated_holding_model = crud.update_portfolio_holding(
        db=db, db_holding=db_holding, holding_in=holding_in
    )

    asset_schema = schemas.Asset.model_validate(updated_holding_model.asset_info)
    holding_response = schemas.PortfolioHolding.model_validate(updated_holding_model)
    holding_response.asset_info = asset_schema

    current_price = get_current_price(
        symbol=updated_holding_model.asset_info.symbol,
        asset_type=updated_holding_model.asset_info.asset_type.value,
    )
    if current_price is not None:
        holding_response.current_price = current_price
        holding_response.current_value = updated_holding_model.quantity * current_price
        purchase_value = (
            updated_holding_model.quantity * updated_holding_model.purchase_price
        )
        holding_response.gain_loss = holding_response.current_value - purchase_value
        if purchase_value > 0:
            holding_response.gain_loss_percent = (
                holding_response.gain_loss / purchase_value
            ) * 100

    return holding_response


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_200_OK)
def delete_user_portfolio_holding(
    *,
    db: Session = Depends(get_db),
    holding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a specific portfolio holding for the current user.
    """
    deleted_holding = crud.remove_portfolio_holding(
        db=db, holding_id=holding_id, user_id=current_user.id
    )
    if not deleted_holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio holding not found or not owned by user.",
        )
    asset_schema = schemas.Asset.model_validate(deleted_holding.asset_info)
    holding_response = schemas.PortfolioHolding.model_validate(deleted_holding)
    holding_response.asset_info = asset_schema
    return holding_response
