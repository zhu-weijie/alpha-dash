# app/api/v1/api.py
from fastapi import APIRouter
from app.api.endpoints import users # Import your users router

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Add other endpoint routers here later
# e.g., api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
