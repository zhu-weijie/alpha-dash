# app/api/v1/api.py
from fastapi import APIRouter
from app.api.endpoints import users, auth, assets, portfolio, market_data

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
