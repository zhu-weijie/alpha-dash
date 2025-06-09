# app/tasks/price_tasks.py
from celery import shared_task
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app import crud
from app.services import financial_data_orchestrator as fds_orchestrator
from app.models import Asset as AssetModel


@shared_task(name="app.tasks.price_tasks.refresh_all_asset_prices_task")
def refresh_all_asset_prices_task():
    print("CELERY_TASK: Starting refresh_all_asset_prices_task...")
    db: Session = SessionLocal()
    try:
        assets: list[AssetModel] = crud.get_assets(db, limit=1000)
        
        if not assets:
            print("CELERY_TASK: No assets found to refresh.")
            return "No assets to refresh."

        refreshed_count = 0
        failed_count = 0
        print(f"CELERY_TASK: Found {len(assets)} assets to refresh prices for.")

        for asset_model in assets:
            print(f"CELERY_TASK: Refreshing price for {asset_model.symbol} (Type: {asset_model.asset_type.value})")
            try:
                price = fds_orchestrator.get_current_price(
                    symbol=asset_model.symbol,
                    asset_type=asset_model.asset_type.value
                )
                if price is not None:
                    print(f"CELERY_TASK: Price for {asset_model.symbol} updated/cached: {price}")
                    refreshed_count += 1
                else:
                    print(f"CELERY_TASK: Failed to get price for {asset_model.symbol}")
                    failed_count += 1
            except Exception as e:
                print(f"CELERY_TASK: Error refreshing price for {asset_model.symbol}: {e}")
                failed_count += 1
        
        result_message = f"CELERY_TASK: Price refresh complete. Refreshed: {refreshed_count}, Failed: {failed_count}."
        print(result_message)
        return result_message
    finally:
        db.close()
