"""
/studio  Endpoint'leri — Async
-------------------------------
POST /api/v1/studio/upload    → 1-4 fotoğraf al, Gemini ile analiz et
POST /api/v1/studio/generate  → Analiz + ortam → 5 açı prompt üret + görüntüleri oluştur

Tasarım kararları:
  • Her iki endpoint de async def — ASGI olay döngüsünü bloklamaz.
  • Senkron Gemini çağrıları asyncio.to_thread() ile threadpool'da koşar,
    böylece uzun süren API çağrısı sırasında FastAPI diğer isteklere yanıt verebilir.
  • /generate SSE (Server-Sent Events) yerine polling-ready bir job_id döndürür;
    5 görüntü paralel olarak asyncio.gather() ile üretilir.
  • Üretilen her görüntü /generated/<job_id>/<n>.png olarak diske yazılır,
    URL liste olarak yanıtta döner.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.config import settings
from app.models.schemas import (
    MultiImageAnalysisResponse,
    WoodAnalysis,
)
from app.services.gemini_client import GeminiClient
from app.services.gemini_service import GeminiService
from app.services.prompt_builder import PromptBuilder, ShootEnvironment, ShotBundle
from app.utils.image_utils import save_image_bytes, validate_image

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Singleton bağımlılıklar  (uygulama ömrü boyunca tek örnek)
# ---------------------------------------------------------------------------

_gemini_service: GeminiService | None = None
_gemini_client: GeminiClient | None = None
_prompt_builder = PromptBuilder()  # durumsuz, paylaşılabilir


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


ServiceDep = Annotated[GeminiService, Depends(get_gemini_service)]
ClientDep = Annotated[GeminiClient, Depends(get_gemini_client)]


# ---------------------------------------------------------------------------
# Yanıt şemaları (bu dosyaya özel, hafif modeller)
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    success: bool = True
    session_id: str
    images_received: int
    analysis: WoodAnalysis
    message: str = "Fotoğraflar analiz edildi."


class GeneratedShotResult(BaseModel):
    index: int
    angle_tr: str
    angle_en: str
    environment: str
    image_url: str          # Boş string = üretim başarısız
    prompt_used: str
    status: str             # "completed" | "failed"
    error: str | None = None


class GenerateResponse(BaseModel):
    success: bool = True
    job_id: str
    environment: str
    shots: list[GeneratedShotResult]
    completed: int
    failed: int
    message: str


# ---------------------------------------------------------------------------
# /upload  — 1-4 fotoğraf yükle ve analiz et
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Fotoğraf Yükle ve Analiz Et",
    description=(
        "1-4 ürün fotoğrafını Gemini Vision ile analiz eder. "
        "Ağaç türü, renk, doku, stil gibi ayrıntıları JSON olarak döndürür. "
        "Dönen `session_id` değeri /generate endpoint'inde kullanılır."
    ),
)
async def upload_and_analyze(
    service: ServiceDep,
    images: list[UploadFile] = File(
        ...,
        description="1-4 ürün fotoğrafı (JPEG/PNG/WEBP, her biri maks 10 MB)",
    ),
    extra_context: str | None = Form(
        None,
        description="Ek bağlam: marka, ağaç türü tahmini, özel not (maks 500 karakter)",
        max_length=500,
    ),
):
    # ── Dosya sayısı kontrolü ─────────────────────────────────────────────
    if not images:
        raise HTTPException(status_code=400, detail="En az 1 fotoğraf gereklidir.")
    if len(images) > 4:
        raise HTTPException(status_code=422, detail="En fazla 4 fotoğraf yüklenebilir.")

    # ── Her dosyayı oku ve doğrula ────────────────────────────────────────
    image_bytes_list: list[bytes] = []
    for i, upload in enumerate(images, start=1):
        raw = await upload.read()
        try:
            validate_image(
                data=raw,
                content_type=upload.content_type or "",
                max_size_mb=settings.MAX_IMAGE_SIZE_MB,
                allowed_types=settings.ALLOWED_IMAGE_TYPES,
            )
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=f"Fotoğraf {i}: {exc.detail}",
            )
        image_bytes_list.append(raw)

    # ── Gemini analizi — threadpool'da çalıştır ───────────────────────────
    # run_in_threadpool: senkron Gemini SDK çağrısını asyncio eventloop'u
    # bloklamadan arka plan thread'inde yürütür.
    try:
        analysis: WoodAnalysis = await run_in_threadpool(
            service.analyze_product_images,
            image_bytes_list,
            extra_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        logger.exception("Gemini analiz hatası")
        raise HTTPException(status_code=503, detail=f"Gemini API hatası: {exc}")

    session_id = str(uuid.uuid4())
    logger.info(
        "Analiz tamamlandı | session=%s | ürün=%s | ağaç=%s",
        session_id,
        analysis.product_name,
        analysis.wood_species,
    )
    return UploadResponse(
        session_id=session_id,
        images_received=len(image_bytes_list),
        analysis=analysis,
    )


# ---------------------------------------------------------------------------
# /generate  — 5 açıda görüntü üret
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="5 Profesyonel Çekim Üret",
    description=(
        "Analiz sonucunu ve kullanıcı ortam tercihini alarak 5 farklı açıda "
        "görüntü üretir. Tüm görüntüler asyncio.gather() ile paralel olarak "
        "üretilir — toplam süre en yavaş tek görüntü kadar sürer."
    ),
)
async def generate_shots(
    client: ClientDep,
    reference_image: UploadFile = File(
        ...,
        description="Referans ürün fotoğrafı (görüntü üretimine rehberlik eder)",
    ),
    analysis_json: str = Form(
        ...,
        description="JSON string — /upload endpoint'inden dönen `analysis` alanı",
    ),
    environment: str = Form(
        "studio",
        description=(
            "Çekim ortamı: studio | nature | home | workshop | "
            "minimalist | luxury | outdoor_cafe"
        ),
    ),
    style_override: str | None = Form(
        None,
        description="Stili geçersiz kıl (rustic, scandinavian, industrial, modern...)",
    ),
):
    import json as _json  # noqa: PLC0415

    # ── Analiz JSON parse ─────────────────────────────────────────────────
    try:
        analysis_dict = _json.loads(analysis_json)
        analysis = WoodAnalysis(**analysis_dict)
    except (_json.JSONDecodeError, Exception) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"analysis_json geçersiz: {exc}",
        )

    # ── Referans görüntüyü oku ────────────────────────────────────────────
    ref_bytes = await reference_image.read()
    try:
        validate_image(
            data=ref_bytes,
            content_type=reference_image.content_type or "",
            max_size_mb=settings.MAX_IMAGE_SIZE_MB,
            allowed_types=settings.ALLOWED_IMAGE_TYPES,
        )
    except HTTPException as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"Referans görüntü: {exc.detail}")

    # ── PromptBuilder ile 5 prompt üret ──────────────────────────────────
    try:
        shots: list[ShotBundle] = _prompt_builder.build(
            analysis=analysis,
            environment=environment,
            style_override=style_override or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prompt üretim hatası: {exc}")

    # ── Çıktı klasörünü hazırla ───────────────────────────────────────────
    job_id = str(uuid.uuid4())
    output_dir = Path(settings.GENERATED_IMAGES_DIR) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Görüntü üretimi başladı | job=%s | ortam=%s", job_id, environment)

    # ── 5 görüntüyü PARALEL üret ──────────────────────────────────────────
    tasks = [
        _generate_one_shot(
            client=client,
            shot=shot,
            ref_bytes=ref_bytes,
            output_dir=output_dir,
        )
        for shot in shots
    ]
    results: list[GeneratedShotResult] = await asyncio.gather(*tasks)

    completed = sum(1 for r in results if r.status == "completed")
    failed = len(results) - completed
    logger.info("Üretim tamamlandı | job=%s | %d/%d başarılı", job_id, completed, len(results))

    return GenerateResponse(
        job_id=job_id,
        environment=environment,
        shots=results,
        completed=completed,
        failed=failed,
        message=f"{completed}/5 çekim başarıyla oluşturuldu.",
    )


# ---------------------------------------------------------------------------
# Yardımcı: tek çekim üret (asyncio.gather içinde çağrılır)
# ---------------------------------------------------------------------------

async def _generate_one_shot(
    client: GeminiClient,
    shot: ShotBundle,
    ref_bytes: bytes,
    output_dir: Path,
) -> GeneratedShotResult:
    """
    Tek bir çekim için görüntü üretir ve diske kaydeder.
    Hata durumunda exception fırlatmaz — status="failed" döner.
    asyncio.gather() içinde paralel çalışır.
    """
    filename = f"shot_{shot.index:02d}_{_safe_name(shot.angle_en)}.png"
    file_path = output_dir / filename

    try:
        # Senkron Gemini çağrısı → threadpool'da
        images: list[bytes] = await run_in_threadpool(
            client.generate_product_image,
            shot.prompt,
            shot.negative_prompt,
            ref_bytes,
            1,
        )
        if not images:
            raise RuntimeError("Boş görüntü listesi döndü.")

        await run_in_threadpool(save_image_bytes, images[0], file_path)
        image_url = f"/generated/{output_dir.name}/{filename}"

        logger.debug("Çekim üretildi: %s → %s", shot.angle_en, image_url)
        return GeneratedShotResult(
            index=shot.index,
            angle_tr=shot.angle_tr,
            angle_en=shot.angle_en,
            environment=shot.environment,
            image_url=image_url,
            prompt_used=shot.prompt,
            status="completed",
        )

    except Exception as exc:
        logger.error("Çekim üretilemedi [%s]: %s", shot.angle_en, exc)
        return GeneratedShotResult(
            index=shot.index,
            angle_tr=shot.angle_tr,
            angle_en=shot.angle_en,
            environment=shot.environment,
            image_url="",
            prompt_used=shot.prompt,
            status="failed",
            error=str(exc),
        )


def _safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text.lower())[:24]
