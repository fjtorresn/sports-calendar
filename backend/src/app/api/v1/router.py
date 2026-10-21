from fastapi import APIRouter
from src.app.api.v1 import sports, events

api_router = APIRouter()

api_router.include_router(sports.router, prefix="/catalog", tags=["Catalog"])

api_router.include_router(events.router, prefix="/events", tags=["Events"])