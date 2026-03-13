"""Health check endpoint."""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.gemini_client import GeminiClient

router = APIRouter()
_client: GeminiClient | None = None


def _get_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


@router.get("/health", response_model=HealthResponse, summary="API Sağlık Kontrolü")
async def health_check():
    """Gemini API bağlantısını ve model erişimini test eder."""
    result = _get_client().health_check()
    return result
