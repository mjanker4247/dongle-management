from fastapi import APIRouter

from app.api import categories, dashboard, dongles, import_routes, locations, pcs, test_modules

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(locations.router)
api_router.include_router(pcs.router)
api_router.include_router(dongles.router)
api_router.include_router(categories.router)
api_router.include_router(test_modules.router)
api_router.include_router(import_routes.router)
