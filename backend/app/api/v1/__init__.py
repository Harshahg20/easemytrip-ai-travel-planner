from fastapi import APIRouter
from . import trips

api_router = APIRouter()

# Include existing routers
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
