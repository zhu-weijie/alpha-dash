# app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.price_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    'refresh-all-asset-prices-every-hour': {
        'task': 'app.tasks.price_tasks.refresh_all_asset_prices_task',
        'schedule': 3600.0,
    },
}
