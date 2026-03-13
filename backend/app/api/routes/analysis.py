"""
Ürün Analizi Endpoint'leri
---------------------------
POST /api/v1/products/analyze        → Fotoğrafı analiz et
POST /api/v1/products/shot-prompts   → 5 çekim açısı promptu üret
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.models.schemas import AnalyzeResponse, ProductAnalysis, ShotPrompt, ShotPromptsResponse
from app.services.gemini_client import GeminiClient
from app.utils.image_utils import validate_image

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency: paylaşılan istemci
# ---------------------------------------------------------------------------

_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


GeminiDep = Annotated[GeminiClient, Depends(get_gemini_client)]


# ---------------------------------------------------------------------------
# 1. Ürün analizi
# ---------------------------------------------------------------------------

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Ürün Fotoğrafını Analiz Et",
    description=(
        "Yüklenen ürün fotoğrafını Gemini Multimodal ile analiz eder. "
        "Renk, malzeme, stil, hedef kitle ve çekim önerilerini döndürür."
    ),
)
async def analyze_product(
    client: GeminiDep,
    image: UploadFile = File(..., description="Ürün fotoğrafı (JPEG/PNG/WEBP, max 10 MB)"),
    extra_context: Optional[str] = Form(
        None, description="Ek bağlam (marka bilgisi, hedef pazar vb.)", max_length=500
    ),
):
    # --- Dosya doğrulama ---
    image_bytes = await image.read()
    validate_image(
        data=image_bytes,
        content_type=image.content_type or "",
        max_size_mb=settings.MAX_IMAGE_SIZE_MB,
        allowed_types=settings.ALLOWED_IMAGE_TYPES,
    )

    # --- Gemini analizi ---
    try:
        raw = client.analyze_product(image_bytes, extra_context)
        analysis = ProductAnalysis(**raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Analiz sırasında hata: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gemini API hatası: {exc}",
        )

    return AnalyzeResponse(analysis=analysis)


# ---------------------------------------------------------------------------
# 2. Çekim açısı promptları
# ---------------------------------------------------------------------------

@router.post(
    "/shot-prompts",
    response_model=ShotPromptsResponse,
    status_code=status.HTTP_200_OK,
    summary="5 Çekim Açısı Promptu Oluştur",
    description=(
        "Ürün fotoğrafı ve analiz sonucuna göre 5 farklı profesyonel çekim "
        "açısı için görüntü üretim promptları oluşturur."
    ),
)
async def generate_shot_prompts(
    client: GeminiDep,
    image: UploadFile = File(..., description="Ürün fotoğrafı"),
    product_name: str = Form(..., description="Ürün adı"),
    category: str = Form(..., description="Ürün kategorisi"),
    style: str = Form("modern", description="Ürün stili"),
    colors: str = Form("", description="Virgülle ayrılmış renk listesi"),
    materials: str = Form("", description="Virgülle ayrılmış malzeme listesi"),
    brand_tone: str = Form("", description="Marka tonu"),
    target_audience: str = Form("", description="Hedef kitle"),
):
    image_bytes = await image.read()
    validate_image(
        data=image_bytes,
        content_type=image.content_type or "",
        max_size_mb=settings.MAX_IMAGE_SIZE_MB,
        allowed_types=settings.ALLOWED_IMAGE_TYPES,
    )

    # Form verilerinden basit analiz nesnesi oluştur
    analysis = {
        "product_name": product_name,
        "category": category,
        "style": style,
        "colors": [c.strip() for c in colors.split(",") if c.strip()],
        "materials": [m.strip() for m in materials.split(",") if m.strip()],
        "brand_tone": brand_tone,
        "target_audience": target_audience,
    }

    try:
        raw_shots = client.generate_shot_prompts(analysis, image_bytes)
        shots = [ShotPrompt(**s) for s in raw_shots]
    except Exception as exc:
        logger.exception("Çekim promptları üretilirken hata: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prompt üretim hatası: {exc}",
        )

    return ShotPromptsResponse(shots=shots)
