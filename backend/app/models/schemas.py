"""
Pydantic Şemaları
-----------------
API istek / yanıt modelleri.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ahşap / Malzeme Detay Analizi  (gemini_service.py çıktısı)
# ---------------------------------------------------------------------------

class WoodGrain(BaseModel):
    """Ahşap doku / damar özellikleri."""
    pattern: str = Field(
        ...,
        description="Damar deseni: straight | wavy | interlocked | irregular | birdseye | quilted",
    )
    visibility: str = Field(
        ...,
        description="Damar belirginliği: subtle | moderate | prominent | very_prominent",
    )
    description: str = Field(..., description="Serbest metin — damarın görsel niteliği")


class WoodFinish(BaseModel):
    """Yüzey işlem bilgisi."""
    type: str = Field(
        ...,
        description="İşlem türü: raw | oiled | waxed | lacquered | stained | painted | burned | distressed",
    )
    sheen: str = Field(
        ...,
        description="Parlaklık: matte | satin | semi_gloss | gloss",
    )
    texture_feel: str = Field(
        ...,
        description="Dokunsal his: silky_smooth | smooth | slightly_textured | rough | hand_carved",
    )


class ColorProfile(BaseModel):
    """Renk profili — prompt zenginleştirme için."""
    primary: str = Field(..., description="Ana renk (CSS renk adı veya tanımlayıcı)")
    secondary: list[str] = Field(default_factory=list, description="Tamamlayıcı / damarlardaki renkler")
    undertone: str = Field(..., description="Alt ton: warm | cool | neutral")
    hex_estimate: Optional[str] = Field(None, description="Tahmini HEX kodu (#RRGGBB)")


class WoodAnalysis(BaseModel):
    """
    1-4 fotoğraftan elde edilen kapsamlı ahşap ürün analizi.
    gemini_service.analyze_product_images() tarafından döndürülür.
    """
    # — Ürün kimliği
    product_name: str = Field(..., description="Ürün adı (masa, sandalye, kase...)")
    product_type: str = Field(..., description="Spesifik tür (dining_table, wall_shelf, salad_bowl...)")
    use_case: str = Field(..., description="functional | decorative | both")
    environment: str = Field(..., description="Kullanım ortamı: indoor | outdoor | both")

    # — Ahşap / malzeme
    wood_species: str = Field(
        ...,
        description="Tahmin edilen ağaç türü (oak, walnut, pine, cherry, ash, teak, mahogany, birch, "
                    "maple, poplar, cedar, mango_wood, acacia, beech, unknown...)",
    )
    wood_species_confidence: str = Field(
        ...,
        description="Tür tahmin güveni: high | medium | low",
    )
    wood_species_alternatives: list[str] = Field(
        default_factory=list,
        description="Alternatif olası türler",
    )
    grain: WoodGrain
    finish: WoodFinish
    color: ColorProfile

    # — Tasarım / işçilik
    style: str = Field(
        ...,
        description="Tasarım stili: rustic | scandinavian | industrial | modern | traditional | "
                    "mid_century | wabi_sabi | bohemian | minimalist | farmhouse",
    )
    craftsmanship: str = Field(
        ...,
        description="İşçilik düzeyi: handmade_artisan | semi_handmade | machine_produced",
    )
    joinery_details: list[str] = Field(
        default_factory=list,
        description="Bağlantı / montaj detayları (dovetail, mortise_tenon, live_edge, epoxy_fill...)",
    )
    distinctive_features: list[str] = Field(
        default_factory=list,
        description="Öne çıkan görsel özellikler (live edge, knots, sapwood streak, burn marks...)",
    )

    # — Boyut tahmini
    size_estimate: str = Field(
        ...,
        description="Boyut tahmini (small / medium / large + açıklama)",
    )

    # — Prompt zenginleştirme
    prompt_keywords: list[str] = Field(
        ...,
        description="Görüntü üretim promptuna eklenecek anahtar kelimeler (İngilizce)",
        min_length=5,
    )
    negative_keywords: list[str] = Field(
        default_factory=list,
        description="Görüntü üretiminde KAÇINILACAk unsurlar (İngilizce)",
    )
    lighting_recommendation: str = Field(
        ...,
        description="Önerilen ışık kurulumu",
    )
    suggested_backgrounds: list[str] = Field(
        default_factory=list,
        description="Arka plan önerileri",
        min_length=3,
    )

    # — Çoklu fotoğraf meta
    images_analyzed: int = Field(..., description="Analize giren fotoğraf sayısı", ge=1, le=4)
    analysis_notes: Optional[str] = Field(
        None,
        description="Modelin ek notları (eksik açı, belirsiz detay vb.)",
    )


class MultiImageAnalysisResponse(BaseModel):
    """gemini_service analyze endpoint yanıtı."""
    success: bool = True
    analysis: WoodAnalysis
    message: str = "Ürün başarıyla analiz edildi."


# ---------------------------------------------------------------------------
# Ürün Analizi  (gemini_client.py — genel amaçlı, geriye dönük uyumluluk)
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
