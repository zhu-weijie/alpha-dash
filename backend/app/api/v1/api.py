# app/api/v1/api.py
from fastapi import APIRouter
from app.api.endpoints import users, auth

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
