from fastapi import APIRouter

api_router = APIRouter()

# Import and include other routers here
from app.api.v1.endpoints import health
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Example:
# from app.api.v1.endpoints import items, users
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(items.router, prefix="/items", tags=["items"]) 