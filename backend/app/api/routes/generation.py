"""
Görüntü Üretimi Endpoint'leri
------------------------------
POST /api/v1/products/generate          → Tüm 5 çekimi üret
POST /api/v1/products/generate/single   → Tek çekim üret
"""

import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.models.schemas import GeneratedShot, GenerateResponse, GenerationStatus
from app.services.gemini_client import GeminiClient
from app.utils.image_utils import save_image_bytes, validate_image

logger = logging.getLogger(__name__)
router = APIRouter()

_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


GeminiDep = Annotated[GeminiClient, Depends(get_gemini_client)]


# ---------------------------------------------------------------------------
# 5 çekim üret
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="5 Profesyonel Çekim Üret",
    description=(
        "JSON dizisi halinde verilen 5 çekim promptu için görüntüler üretir. "
        "Her görüntü sunucuya kaydedilir ve URL olarak döndürülür."
    ),
)
async def generate_all_shots(
    client: GeminiDep,
    image: UploadFile = File(..., description="Referans ürün fotoğrafı"),
    shots_json: str = Form(
        ...,
        description=(
            'JSON dizisi: [{"angle":"...","prompt":"...","negative_prompt":"..."}]'
        ),
    ),
):
    import json  # noqa: PLC0415

    # --- Görüntü doğrulama ---
    image_bytes = await image.read()
    validate_image(
        data=image_bytes,
        content_type=image.content_type or "",
        max_size_mb=settings.MAX_IMAGE_SIZE_MB,
        allowed_types=settings.ALLOWED_IMAGE_TYPES,
    )

    # --- JSON parse ---
    try:
        shot_list: list[dict] = json.loads(shots_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"shots_json geçersiz JSON: {exc}",
        )

    if not shot_list or len(shot_list) > 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="shots_json 1-10 eleman içermeli.",
        )

    product_id = str(uuid.uuid4())
    output_dir = Path(settings.GENERATED_IMAGES_DIR) / product_id
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_shots: list[GeneratedShot] = []

    for idx, shot in enumerate(shot_list):
        angle = shot.get("angle", f"Çekim {idx + 1}")
        prompt = shot.get("prompt", "")
        negative_prompt = shot.get("negative_prompt", "")

        if not prompt:
            logger.warning("Çekim %d için prompt boş, atlanıyor.", idx + 1)
            continue

        try:
            images = client.generate_product_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                reference_image=image_bytes,
                number_of_images=1,
            )
            if not images:
                raise RuntimeError("Boş görüntü listesi döndü.")

            filename = f"shot_{idx + 1:02d}_{_safe_name(angle)}.png"
            file_path = output_dir / filename
            save_image_bytes(images[0], file_path)

            image_url = f"/generated/{product_id}/{filename}"
            generated_shots.append(
                GeneratedShot(
                    angle=angle,
                    image_url=image_url,
                    prompt_used=prompt,
                    status=GenerationStatus.COMPLETED,
                )
            )
            logger.info("Çekim üretildi: %s → %s", angle, image_url)

        except Exception as exc:
            logger.error("Çekim üretilemedi (%s): %s", angle, exc)
            generated_shots.append(
                GeneratedShot(
                    angle=angle,
                    image_url="",
                    prompt_used=prompt,
                    status=GenerationStatus.FAILED,
                )
            )

    success_count = sum(1 for s in generated_shots if s.status == GenerationStatus.COMPLETED)

    return GenerateResponse(
        product_id=product_id,
        shots=generated_shots,
        message=f"{success_count}/{len(shot_list)} çekim başarıyla oluşturuldu.",
    )


# ---------------------------------------------------------------------------
# Tek çekim üret
# ---------------------------------------------------------------------------

@router.post(
    "/generate/single",
    response_model=GeneratedShot,
    status_code=status.HTTP_200_OK,
    summary="Tek Çekim Üret",
)
async def generate_single_shot(
    client: GeminiDep,
    image: UploadFile = File(..., description="Referans ürün fotoğrafı"),
    angle: str = Form(..., description="Çekim açısı adı"),
    prompt: str = Form(..., description="Görüntü üretim promptu", max_length=2000),
    negative_prompt: str = Form("", description="Kaçınılacak unsurlar", max_length=500),
):
    image_bytes = await image.read()
    validate_image(
        data=image_bytes,
        content_type=image.content_type or "",
        max_size_mb=settings.MAX_IMAGE_SIZE_MB,
        allowed_types=settings.ALLOWED_IMAGE_TYPES,
    )

    try:
        images = client.generate_product_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            reference_image=image_bytes,
            number_of_images=1,
        )
        shot_id = str(uuid.uuid4())[:8]
        filename = f"{shot_id}_{_safe_name(angle)}.png"
        file_path = Path(settings.GENERATED_IMAGES_DIR) / filename
        save_image_bytes(images[0], file_path)
        image_url = f"/generated/{filename}"
    except Exception as exc:
        logger.exception("Tek çekim üretilemedi: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return GeneratedShot(
        angle=angle,
        image_url=image_url,
        prompt_used=prompt,
        status=GenerationStatus.COMPLETED,
    )


# ---------------------------------------------------------------------------
# Yardımcı
# ---------------------------------------------------------------------------

def _safe_name(text: str) -> str:
    """Dosya adı için güvenli string."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text.lower())[:30]
