# app/api/endpoints/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any

from app import crud, models, schemas
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user
from app.services import financial_data_service as fds

router = APIRouter()

@router.post("/holdings/", response_model=schemas.PortfolioHolding, status_code=status.HTTP_201_CREATED)
def add_asset_to_portfolio(
    *,
    db: Session = Depends(get_db),
    holding_in: schemas.PortfolioHoldingCreate,
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Add an asset holding to the current user's portfolio.
    """
    # Validate that the asset_id refers to an existing asset
    asset = crud.get_asset(db, asset_id=holding_in.asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with ID {holding_in.asset_id} not found.",
        )
    holding_model = crud.create_portfolio_holding(
        db=db, holding_in=holding_in, user_id=current_user.id
    )
    # Manually construct the response schema with asset_info
    # This ensures asset_info is populated for the immediate response after creation
    asset_schema = schemas.Asset.model_validate(holding_model.asset_info)
    holding_response = schemas.PortfolioHolding.model_validate(holding_model)
    holding_response.asset_info = asset_schema
    
    # Fetch current price for the newly added holding for immediate display if desired
    current_price = fds.fetch_current_price(holding_model.asset_info.symbol)
    if current_price is not None:
        holding_response.current_price = current_price
        holding_response.current_value = holding_model.quantity * current_price
        purchase_value = holding_model.quantity * holding_model.purchase_price
        holding_response.gain_loss = holding_response.current_value - purchase_value
        if purchase_value > 0: # Avoid division by zero
            holding_response.gain_loss_percent = (holding_response.gain_loss / purchase_value) * 100

    return holding_response

@router.get("/holdings/", response_model=schemas.PortfolioSummary)
def view_user_portfolio_summary(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0), # Pagination might apply to holdings list within summary
    limit: int = Query(100, ge=1, le=200),
    current_user: models.User = Depends(get_current_active_user)
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
        # Convert DB model to Pydantic schema
        holding_schema = schemas.PortfolioHolding.model_validate(db_holding)
        
        # Ensure asset_info is populated (it should be due to joinedload)
        if db_holding.asset_info:
            holding_schema.asset_info = schemas.Asset.model_validate(db_holding.asset_info)
            
            # Fetch current price for the asset
            current_price = fds.fetch_current_price(db_holding.asset_info.symbol)
            
            purchase_value_of_holding = db_holding.quantity * db_holding.purchase_price
            total_purchase_value += purchase_value_of_holding

            if current_price is not None:
                holding_schema.current_price = current_price
                current_value_of_holding = db_holding.quantity * current_price
                holding_schema.current_value = current_value_of_holding
                holding_schema.gain_loss = current_value_of_holding - purchase_value_of_holding
                if purchase_value_of_holding > 0:
                    holding_schema.gain_loss_percent = (holding_schema.gain_loss / purchase_value_of_holding) * 100
                else:
                    holding_schema.gain_loss_percent = 0.0 if current_value_of_holding == 0 else None # Handle 0 purchase price
                total_current_value += current_value_of_holding
            else:
                # If price fetch fails, current_value and gain_loss remain None (as per schema default)
                # You might decide to add the purchase value to total_current_value
                # or handle it differently, e.g., exclude from total_current_value calculation.
                # For simplicity, if current price is unknown, it doesn't contribute to total_current_value.
                pass
        
        processed_holdings.append(holding_schema)

    total_gain_loss = total_current_value - total_purchase_value
    total_gain_loss_percent = 0.0
    if total_purchase_value > 0:
        total_gain_loss_percent = (total_gain_loss / total_purchase_value) * 100
    elif total_current_value > 0 : # Purchased for 0, but has value now (e.g. airdrop)
         total_gain_loss_percent = float('inf') # Or handle as 100% gain if current_value > 0

    return schemas.PortfolioSummary(
        total_purchase_value=round(total_purchase_value, 2),
        total_current_value=round(total_current_value, 2),
        total_gain_loss=round(total_gain_loss, 2),
        total_gain_loss_percent=round(total_gain_loss_percent, 2) if total_gain_loss_percent != float('inf') else None,
        holdings=processed_holdings
    )

@router.get("/holdings/{holding_id}", response_model=schemas.PortfolioHolding)
def view_single_portfolio_holding(
    *,
    db: Session = Depends(get_db),
    holding_id: int,
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    db_holding = crud.get_portfolio_holding(db=db, holding_id=holding_id, user_id=current_user.id)
    if not db_holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio holding not found or not owned by user.")

    holding_response = schemas.PortfolioHolding.model_validate(db_holding)
    if db_holding.asset_info:
        holding_response.asset_info = schemas.Asset.model_validate(db_holding.asset_info)
        current_price = fds.fetch_current_price(db_holding.asset_info.symbol)
        if current_price is not None:
            holding_response.current_price = current_price
            holding_response.current_value = db_holding.quantity * current_price
            purchase_value = db_holding.quantity * db_holding.purchase_price
            holding_response.gain_loss = holding_response.current_value - purchase_value
            if purchase_value > 0:
                holding_response.gain_loss_percent = (holding_response.gain_loss / purchase_value) * 100
    return holding_response
