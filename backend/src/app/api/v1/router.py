from fastapi import APIRouter

from app.api.v1 import catalog, events

api_router = APIRouter()

api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])

api_router.include_router(events.router, prefix="/events", tags=["Events"])
