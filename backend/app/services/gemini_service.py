"""
Gemini Product Analysis Service
---------------------------------
gemini_client.GeminiClient'ın üzerine oturan yüksek seviyeli servis.

Temel fark:
  • 1-4 fotoğrafı TEK Gemini çağrısında birlikte analiz eder
    (model görüntüler arası korelasyon kurar: 1. foto genel görünüm,
     2. foto tahta damarı yakın çekim, 3. foto alt taraf vs.)
  • Ahşap/malzeme odaklı zenginleştirilmiş JSON şeması döndürür
  • prompt_builder.PromptBuilder ile doğrudan entegre çalışır

Kullanım:
    service = GeminiService()
    result: WoodAnalysis = service.analyze_product_images(
        images=[bytes1, bytes2],           # 1-4 fotoğraf
        extra_context="El yapımı ceviz masa",
    )
"""

import json
import logging
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.models.schemas import WoodAnalysis
from app.services.gemini_client import (
    SAFETY_SETTINGS,
    _image_to_part,
    _load_and_validate_image,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------

MAX_IMAGES = 4
MIN_IMAGES = 1

# Analiz için düşük sıcaklık → tutarlı, tekrarlanabilir JSON çıktısı
_ANALYSIS_CONFIG = genai.GenerationConfig(
    temperature=0.2,
    top_p=0.95,
    top_k=32,
    max_output_tokens=3072,
    response_mime_type="application/json",
)

# ---------------------------------------------------------------------------
# JSON şema açıklaması (prompt'a gömülür)
# ---------------------------------------------------------------------------

_JSON_SCHEMA = """{
  "product_name": "<ürün adı, örn: 'Ceviz Yemek Masası'>",
  "product_type": "<spesifik tür, örn: dining_table | wall_shelf | salad_bowl | cutting_board | chair | stool | cabinet | frame | tray | lamp_base | vase | toy | other>",
  "use_case": "<functional | decorative | both>",
  "environment": "<indoor | outdoor | both>",

  "wood_species": "<en olası ağaç türü: oak | walnut | pine | cherry | ash | teak | mahogany | birch | maple | poplar | cedar | mango_wood | acacia | beech | elm | rosewood | unknown>",
  "wood_species_confidence": "<high | medium | low>",
  "wood_species_alternatives": ["<alternatif tür 1>", "<alternatif tür 2>"],

  "grain": {
    "pattern": "<straight | wavy | interlocked | irregular | birdseye | quilted | flame>",
    "visibility": "<subtle | moderate | prominent | very_prominent>",
    "description": "<damarın serbest metin tanımı, örn: 'belirgin düz damar hatları, açık kahve zemin üzerinde koyu çizgiler'>"
  },

  "finish": {
    "type": "<raw | oiled | waxed | lacquered | stained | painted | burned | distressed | natural>",
    "sheen": "<matte | satin | semi_gloss | gloss>",
    "texture_feel": "<silky_smooth | smooth | slightly_textured | rough | hand_carved>"
  },

  "color": {
    "primary": "<ana renk adı, örn: 'warm honey brown'>",
    "secondary": ["<damarlardaki veya sapwood'daki renk>"],
    "undertone": "<warm | cool | neutral>",
    "hex_estimate": "<tahmini HEX, örn: #8B5E3C, veya null>"
  },

  "style": "<rustic | scandinavian | industrial | modern | traditional | mid_century | wabi_sabi | bohemian | minimalist | farmhouse | japandi>",
  "craftsmanship": "<handmade_artisan | semi_handmade | machine_produced>",
  "joinery_details": ["<görünür bağlantı detayları: dovetail | mortise_tenon | live_edge | epoxy_fill | butterfly_key | butt_joint | dado | rabbet | pegged | hand_carved_joints>"],
  "distinctive_features": ["<görsel öne çıkan unsurlar: live_edge | natural_knots | sapwood_streak | wormholes | mineral_stain | cracks_filled_with_epoxy | burn_marks | bark_inclusion>"],

  "size_estimate": "<small (<30cm) | medium (30-100cm) | large (>100cm)  + kısa boyut tahmini>",

  "prompt_keywords": [
    "<görüntü üretim promptuna eklenecek en az 8 İngilizce anahtar kelime>",
    "<örn: 'solid walnut wood', 'live edge', 'hand-oiled finish', 'visible wood grain'>"
  ],
  "negative_keywords": [
    "<kaçınılacak unsurlar, örn: 'plastic', 'glossy artificial surface', 'low quality'>"
  ],

  "lighting_recommendation": "<önerilen ışık kurulumu>",
  "suggested_backgrounds": [
    "<arka plan önerisi 1>",
    "<arka plan önerisi 2>",
    "<arka plan önerisi 3>"
  ],

  "images_analyzed": <kaç fotoğraf analiz edildiği (int)>,
  "analysis_notes": "<modelin ek notları veya null>"
}"""


# ---------------------------------------------------------------------------
# Servis sınıfı
# ---------------------------------------------------------------------------

class GeminiService:
    """
    1-4 ürün fotoğrafını Gemini Vision ile analiz eden yüksek seviyeli servis.

    Tek Gemini çağrısında tüm fotoğrafları gönderir; bu sayede model
    görüntüler arasındaki bağlamı (açı, ışık, yakın/uzak çekim) birleştirir.
    """

    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_VISION_MODEL,
            generation_config=_ANALYSIS_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        )
        logger.info("GeminiService hazır | model=%s", settings.GEMINI_VISION_MODEL)

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def analyze_product_images(
        self,
        images: list[bytes],
        extra_context: Optional[str] = None,
    ) -> WoodAnalysis:
        """
        1-4 ürün fotoğrafını tek Gemini çağrısında analiz eder.

        Args:
            images:        Ham görüntü byte'ları listesi (1-4 öğe).
            extra_context: Kullanıcının eklediği ek bilgi
                           (örn: "El yapımı ceviz masa, Türkiye üretimi").

        Returns:
            WoodAnalysis  Pydantic modeli — prompt_builder için kullanıma hazır.

        Raises:
            ValueError:   Görüntü sayısı veya formatı hatalıysa.
            RuntimeError: Gemini API yanıtı boş veya parse edilemiyorsa.
        """
        self._validate_image_list(images)

        # Her görüntüyü doğrula ve Gemini inline_data formatına dönüştür
        image_parts = []
        for idx, raw in enumerate(images):
            data, mime = _load_and_validate_image(raw)
            image_parts.append(_image_to_part(data, mime))
            logger.debug("Görüntü %d/%d hazırlandı | mime=%s | %.1f KB",
                         idx + 1, len(images), mime, len(data) / 1024)

        # Prompt oluştur ve Gemini'ye gönder
        prompt = self._build_prompt(n_images=len(images), extra_context=extra_context)
        content_parts = [prompt] + image_parts

        logger.info("%d fotoğraf için ürün analizi başlatılıyor...", len(images))
        response = self._model.generate_content(content_parts)

        if not response.text:
            raise RuntimeError(
                "Gemini API boş yanıt döndürdü. "
                "Görüntüler güvenlik filtrelerini tetiklemiş olabilir."
            )

        raw_dict = self._parse_response(response.text)
        raw_dict["images_analyzed"] = len(images)  # gerçek değeri zorla

        return WoodAnalysis(**raw_dict)

    # ------------------------------------------------------------------
    # Dahili yardımcılar
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_image_list(images: list[bytes]) -> None:
        if not images:
            raise ValueError("En az 1 fotoğraf gereklidir.")
        if len(images) > MAX_IMAGES:
            raise ValueError(
                f"En fazla {MAX_IMAGES} fotoğraf yüklenebilir "
                f"(gönderilen: {len(images)})."
            )
        for i, img in enumerate(images):
            if not img:
                raise ValueError(f"Fotoğraf {i + 1} boş.")

    @staticmethod
    def _build_prompt(n_images: int, extra_context: Optional[str]) -> str:
        """
        Çok-görüntülü analiz talimatını oluşturur.
        Model kaç fotoğraf gördüğünü ve her birinden ne çıkarması
        gerektiğini açıkça bilir.
        """
        image_hints = {
            1: "Tek bir fotoğraf var; mümkün olduğu kadar çok detay çıkar.",
            2: "İki fotoğraf var. Birbirini tamamlayan açıları karşılaştır.",
            3: "Üç fotoğraf var. Genel görünüm, detay ve farklı açıları birleştir.",
            4: "Dört fotoğraf var. 360° bağlam kurmak için tüm açıları sentezle.",
        }

        extra = f"\n\nKullanıcı ek bilgi verdi: {extra_context}" if extra_context else ""

        return f"""Sen ahşap mobilya ve el yapımı ahşap ürünler konusunda uzman,
deneyimli bir ürün fotoğrafçısı ve malzeme analistisin.

Sana {n_images} adet ürün fotoğrafı gösteriliyor.
{image_hints[n_images]}

GÖREVİN:
Fotoğrafları birlikte değerlendirerek aşağıdaki JSON şemasını EKSIKSIZ doldur.
— YALNIZCA JSON döndür, başka açıklama veya markdown ekleme.
— Tahmin edemediğin alanlar için "unknown" yaz, boş bırakma.
— prompt_keywords: görüntü üretim AI'ına verilecek, ürünü doğru tarif eden
  İngilizce anahtar kelimeler (en az 8 adet).
— Ahşap türü tespitinde: renk tonu, damar deseni, yüzey dokusu ve işçilik
  ipuçlarını birlikte kullan.{extra}

JSON ŞEMASI:
{_JSON_SCHEMA}"""

    @staticmethod
    def _parse_response(text: str) -> dict:
        """
        Gemini yanıtını JSON dict'e dönüştürür.
        Model bazen ```json ... ``` bloğu döndürür — bunu temizler.
        """
        cleaned = text.strip()

        # Markdown kod bloğunu kaldır
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            # İlk ve son ``` satırlarını at
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            cleaned = "\n".join(inner).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # Son çare: ilk { ... } bloğunu bul
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass
            raise RuntimeError(
                f"Gemini yanıtı JSON'a parse edilemedi: {exc}\n"
                f"Yanıt önizleme: {text[:300]}"
            ) from exc
