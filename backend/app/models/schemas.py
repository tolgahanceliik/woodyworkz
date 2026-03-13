"""
Pydantic Şemaları
-----------------
API istek / yanıt modelleri.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ürün Analizi
# ---------------------------------------------------------------------------

class ProductAnalysis(BaseModel):
    """Gemini'nin ürün analizi çıktısı."""
    product_name: str = Field(..., description="Tahmin edilen ürün adı")
    category: str = Field(..., description="Ürün kategorisi")
    colors: list[str] = Field(default_factory=list, description="Tespit edilen renkler")
    materials: list[str] = Field(default_factory=list, description="Tespit edilen malzemeler")
    style: str = Field(..., description="Stil tanımı (modern, minimalist, lüks...)")
    key_features: list[str] = Field(default_factory=list, description="Öne çıkan özellikler")
    suggested_backgrounds: list[str] = Field(default_factory=list, description="Arka plan önerileri")
    lighting_recommendation: str = Field(..., description="Işık önerisi")
    target_audience: str = Field(..., description="Hedef kitle")
    brand_tone: str = Field(..., description="Marka tonu")


class AnalyzeRequest(BaseModel):
    """Analiz endpoint'i için ek parametreler (form alanı olarak gelebilir)."""
    extra_context: Optional[str] = Field(
        None,
        description="Modele verilecek ek bağlam (marka bilgisi, hedef pazar vb.)",
        max_length=500,
    )


class AnalyzeResponse(BaseModel):
    """Analiz endpoint'i yanıtı."""
    success: bool = True
    analysis: ProductAnalysis
    message: str = "Ürün başarıyla analiz edildi."


# ---------------------------------------------------------------------------
# Çekim Açıları
# ---------------------------------------------------------------------------

class ShotPrompt(BaseModel):
    """Tek bir çekim açısı için üretilmiş prompt."""
    angle: str = Field(..., description="Çekim açısı adı (Türkçe)")
    description: str = Field(..., description="Açının amacı")
    prompt: str = Field(..., description="Görüntü üretim promptu (İngilizce)")
    negative_prompt: str = Field(default="", description="Kaçınılacak unsurlar (İngilizce)")


class ShotPromptsResponse(BaseModel):
    """5 çekim açısı promptları yanıtı."""
    success: bool = True
    shots: list[ShotPrompt]
    message: str = "Çekim promptları başarıyla oluşturuldu."


# ---------------------------------------------------------------------------
# Görüntü Üretimi
# ---------------------------------------------------------------------------

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedShot(BaseModel):
    """Tek bir üretilmiş çekim."""
    angle: str
    image_url: str = Field(..., description="Üretilen görüntünün URL'i")
    prompt_used: str
    status: GenerationStatus = GenerationStatus.COMPLETED


class GenerateResponse(BaseModel):
    """Görüntü üretim endpoint'i yanıtı."""
    success: bool = True
    product_id: str = Field(..., description="Bu ürün oturumunun benzersiz ID'si")
    shots: list[GeneratedShot]
    message: str = "Profesyonel çekimler başarıyla oluşturuldu."


# ---------------------------------------------------------------------------
# Hata yanıtları
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    vision_model: str
    text_model: str
    image_gen_model: str
    image_gen_available: bool
    test_response: Optional[str] = None
    error: Optional[str] = None
