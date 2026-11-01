from fastapi import APIRouter

from app.routes import auth, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(reports.router)

__all__ = ["api_router"]
