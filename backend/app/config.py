"""
Uygulama Konfigürasyonu
------------------------
Tüm ortam değişkenleri burada merkezi olarak yönetilir.
.env dosyasından veya sistem ortamından okunur.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Gemini API
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str

    # Multimodal analiz + vision
    GEMINI_VISION_MODEL: str = "gemini-1.5-pro"

    # Metin üretimi (prompt yazımı vb.)
    GEMINI_TEXT_MODEL: str = "gemini-1.5-flash"

    # Görüntü üretimi — önce Imagen 3, fallback Gemini 2.0 Flash
    GEMINI_IMAGE_GEN_MODEL: str = "imagen-3.0-generate-001"

    # ------------------------------------------------------------------
    # FastAPI
    # ------------------------------------------------------------------
    APP_NAME: str = "WoodyWorkz AI Product Studio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # CORS — frontend URL'leri
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA / Next.js
        "http://localhost:8080",
    ]

    # ------------------------------------------------------------------
    # Dosya yükleme
    # ------------------------------------------------------------------
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # ------------------------------------------------------------------
    # Üretim çıktısı
    # ------------------------------------------------------------------
    GENERATED_IMAGES_DIR: str = "generated_images"
    SHOTS_PER_PRODUCT: int = 5          # Her ürün için üretilecek çekim sayısı

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings nesnesi döndürür (test override'ı için cache_clear kullan)."""
    return Settings()


# Modül seviyesinde kolay erişim
settings = get_settings()
