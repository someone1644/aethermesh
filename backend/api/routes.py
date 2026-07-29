from fastapi import APIRouter
from api.schemas import HealthResponse
from config import settings
router = APIRouter()
@router.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="running",
        version=settings.VERSION,
    )
@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
    }