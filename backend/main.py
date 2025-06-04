# backend/main.py
from fastapi import FastAPI
from app.core.config import settings # Import the settings instance

app = FastAPI(
    title=settings.PROJECT_NAME, # Uses PROJECT_NAME from your config
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/")
async def root():
    # Uses PROJECT_NAME from your config
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# Simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "project_name": settings.PROJECT_NAME}

# Placeholder for API router - we will add this later
# We will create app/api/v1/api.py and uncomment/add the lines below in a future step
# from app.api.v1.api import api_router as api_v1_router
# app.include_router(api_v1_router, prefix=settings.API_V1_STR)
