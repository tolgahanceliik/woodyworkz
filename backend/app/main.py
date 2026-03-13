"""
WoodyWorkz AI Product Studio — FastAPI Uygulaması
--------------------------------------------------
Başlatma: uvicorn app.main:app --reload
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import analysis, generation, health, studio

# ---------------------------------------------------------------------------
# Loglama
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: uygulama başlangıç / kapatma
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Başlangıç
    logger.info("🚀 %s v%s başlatılıyor...", settings.APP_NAME, settings.APP_VERSION)

    # Üretilen görseller için klasör oluştur
    output_dir = Path(settings.GENERATED_IMAGES_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Çıktı klasörü: %s", output_dir.resolve())

    yield  # Uygulama çalışıyor

    # Kapatma
    logger.info("Uygulama kapatılıyor...")


# ---------------------------------------------------------------------------
# FastAPI uygulaması
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Ürün fotoğraflarını Gemini AI ile analiz eden ve "
        "5 farklı açıdan profesyonel çekimler üreten API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router'lar
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(analysis.router, prefix="/api/v1/products", tags=["Product Analysis"])
app.include_router(generation.router, prefix="/api/v1/products", tags=["Image Generation"])
app.include_router(studio.router, prefix="/api/v1/studio", tags=["Studio — Multi-Image"])

# ---------------------------------------------------------------------------
# Statik dosyalar (üretilen görseller)
# ---------------------------------------------------------------------------
static_dir = Path(settings.GENERATED_IMAGES_DIR)
static_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/generated",
    StaticFiles(directory=str(static_dir)),
    name="generated",
)


# ---------------------------------------------------------------------------
# Kök endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
