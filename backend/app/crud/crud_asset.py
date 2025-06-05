# app/crud/crud_asset.py
from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from app import models, schemas

def get_asset(db: Session, asset_id: int) -> Optional[models.Asset]:
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()

def get_asset_by_symbol(db: Session, symbol: str) -> Optional[models.Asset]:
    return db.query(models.Asset).filter(models.Asset.symbol == symbol.upper()).first()

def get_assets(db: Session, skip: int = 0, limit: int = 100) -> List[models.Asset]:
    return db.query(models.Asset).offset(skip).limit(limit).all()

def create_asset(db: Session, *, asset_in: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(
        symbol=asset_in.symbol.upper(), # Store symbols in uppercase for consistency
        name=asset_in.name,
        asset_type=asset_in.asset_type
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def update_asset(
    db: Session, *, db_obj: models.Asset, obj_in: Union[schemas.AssetUpdate, Dict[str, Any]]
) -> models.Asset:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True) # Pydantic V2, was .dict()
    
    if "symbol" in update_data: # Ensure symbol is also uppercased on update
        update_data["symbol"] = update_data["symbol"].upper()

    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj) # or db.merge(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def remove_asset(db: Session, *, asset_id: int) -> Optional[models.Asset]:
    db_obj = db.query(models.Asset).get(asset_id) # .get() is efficient for PK lookup
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj # Returns the deleted object or None if not found
