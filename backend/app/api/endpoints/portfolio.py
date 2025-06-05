# app/api/endpoints/portfolio.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any

from app import crud, models, schemas
from app.db.session import get_db
from app.auth.dependencies import get_current_active_user

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
    
    # Optional: Check if user already holds this specific asset.
    # Depending on desired logic, you might want to update quantity or disallow duplicates.
    # For now, we allow multiple holding entries for the same asset (e.g., bought at different times).

    holding = crud.create_portfolio_holding(
        db=db, holding_in=holding_in, user_id=current_user.id
    )
    # To ensure asset_info is populated in the response, reload if necessary or rely on schema config
    # If using joinedload in CRUD, it should be populated. Let's test.
    # Alternatively, explicitly fetch it for the response:
    db.refresh(holding) # Make sure relationships are loaded if not already
    if not holding.asset_info: # If eager loading didn't catch it or for direct creation response
        holding.asset_info = crud.get_asset(db, asset_id=holding.asset_id)

    return holding

@router.get("/holdings/", response_model=List[schemas.PortfolioHolding])
def view_user_portfolio(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve the current user's portfolio holdings.
    """
    holdings = crud.get_portfolio_holdings_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return holdings

@router.get("/holdings/{holding_id}", response_model=schemas.PortfolioHolding)
def view_single_portfolio_holding(
    *,
    db: Session = Depends(get_db),
    holding_id: int,
    current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Retrieve a specific holding from the current user's portfolio.
    """
    holding = crud.get_portfolio_holding(db=db, holding_id=holding_id, user_id=current_user.id)
    if not holding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio holding not found or not owned by user.")
    return holding
