# app/tasks/price_tasks.py
from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app import crud
from app.services import financial_data_orchestrator as fds_orchestrator
from app.models import Asset as AssetModel

PRICE_STALENESS_THRESHOLD_MINUTES = 30


@shared_task(name="app.tasks.price_tasks.refresh_all_asset_prices_task")
def refresh_all_asset_prices_task():
    print("CELERY_TASK: Starting refresh_all_asset_prices_task (enhanced)...")
    db: Session = SessionLocal()
    try:
        assets_to_check: list[AssetModel] = crud.get_assets(db, limit=10000)

        if not assets_to_check:
            print("CELERY_TASK: No assets found in DB to refresh.")
            return "No assets to refresh."

        refreshed_count = 0
        skipped_count = 0
        failed_count = 0
        now_utc = datetime.now(timezone.utc)
        staleness_delta = timedelta(minutes=PRICE_STALENESS_THRESHOLD_MINUTES)

        print(
            f"CELERY_TASK: Checking {len(assets_to_check)} assets for price refresh..."
        )

        for asset_model in assets_to_check:
            should_refresh = False
            if asset_model.last_price_updated_at is None:
                should_refresh = True
                print(
                    f"CELERY_TASK: Asset {asset_model.symbol} - Refreshing (never updated)."
                )
            else:
                if now_utc - asset_model.last_price_updated_at > staleness_delta:
                    should_refresh = True
                    print(
                        f"CELERY_TASK: Asset {asset_model.symbol} - Refreshing (stale: last updated {asset_model.last_price_updated_at})."
                    )
                else:
                    print(
                        f"CELERY_TASK: Asset {asset_model.symbol} - Skipping (fresh: last updated {asset_model.last_price_updated_at})."
                    )
                    skipped_count += 1

            if should_refresh:
                try:
                    print(
                        f"CELERY_TASK: Fetching price for {asset_model.symbol} (Type: {asset_model.asset_type.value})"
                    )
                    price = fds_orchestrator.get_current_price(
                        symbol=asset_model.symbol,
                        asset_type=asset_model.asset_type.value,
                    )
                    if price is not None:
                        crud.update_asset_last_price_timestamp(
                            db=db, asset_model=asset_model, timestamp=now_utc
                        )
                        print(
                            f"CELERY_TASK: Price for {asset_model.symbol} updated/cached: {price}. DB timestamp updated."
                        )
                        refreshed_count += 1
                    else:
                        print(
                            f"CELERY_TASK: Failed to get price for {asset_model.symbol} (orchestrator returned None)."
                        )
                        failed_count += 1
                except Exception as e:
                    print(
                        f"CELERY_TASK: ERROR processing asset {asset_model.symbol}: {e}"
                    )
                    failed_count += 1

        result_message = (
            f"CELERY_TASK: Price refresh complete. "
            f"Refreshed: {refreshed_count}, Skipped (fresh): {skipped_count}, Failed: {failed_count}."
        )
        print(result_message)
        return result_message
    except Exception as e:
        print(f"CELERY_TASK: CRITICAL ERROR in refresh_all_asset_prices_task: {e}")
        return f"Task failed with critical error: {e}"
    finally:
        db.close()
