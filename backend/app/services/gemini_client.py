"""
Gemini API Client
-----------------
Google Gemini API ile bağlantı kuran merkezi istemci.
Hem multimodal analiz (görüntü + metin) hem de
görüntü üretimi (Imagen / Gemini 2.0 Flash) destekler.
"""

import base64
import io
import logging
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safety ayarları — ürün fotoğrafları için makul varsayılanlar
# ---------------------------------------------------------------------------
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# ---------------------------------------------------------------------------
# Generation konfigürasyonu
# ---------------------------------------------------------------------------
ANALYSIS_GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.4,      # analiz için düşük yaratıcılık → tutarlı çıktı
    top_p=0.95,
    top_k=40,
    max_output_tokens=2048,
    response_mime_type="application/json",
)

DESCRIPTION_GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.7,      # prompt üretimi için biraz daha yaratıcı
    top_p=0.95,
    top_k=40,
    max_output_tokens=1024,
)


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _image_to_part(image_data: bytes, mime_type: str = "image/jpeg") -> dict:
    """Ham byte → Gemini inline_data formatı."""
    return {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(image_data).decode("utf-8"),
        }
    }


def _load_and_validate_image(image_data: bytes) -> tuple[bytes, str]:
    """
    Görüntüyü doğrular, gerekirse JPEG'e dönüştürür.
    Returns: (bytes, mime_type)
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        fmt = (img.format or "JPEG").upper()
        mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
        mime_type = mime_map.get(fmt, "image/jpeg")

        # RGBA / palette modlarını RGB'ye çevir (JPEG uyumu)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=92)
            return buf.getvalue(), "image/jpeg"

        return image_data, mime_type
    except Exception as exc:
        raise ValueError(f"Geçersiz görüntü formatı: {exc}") from exc


# ---------------------------------------------------------------------------
# Ana istemci sınıfı
# ---------------------------------------------------------------------------

class GeminiClient:
    """
    Google Gemini API sarmalayıcısı.

    Kullanım:
        client = GeminiClient()
        result = await client.analyze_product(image_bytes)
    """

    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Multimodal analiz modeli
        self.vision_model = genai.GenerativeModel(
            model_name=settings.GEMINI_VISION_MODEL,
            generation_config=ANALYSIS_GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        )

        # Prompt üretimi için metin modeli
        self.text_model = genai.GenerativeModel(
            model_name=settings.GEMINI_TEXT_MODEL,
            generation_config=DESCRIPTION_GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        )

        # Görüntü üretimi için model (Imagen 3 veya Gemini 2.0 Flash)
        self._init_image_generation_model()

        logger.info(
            "GeminiClient hazır | vision=%s | text=%s | image_gen=%s",
            settings.GEMINI_VISION_MODEL,
            settings.GEMINI_TEXT_MODEL,
            settings.GEMINI_IMAGE_GEN_MODEL,
        )

    def _init_image_generation_model(self) -> None:
        """Görüntü üretim modelini başlat."""
        try:
            self.image_gen_model = genai.ImageGenerationModel(
                model_name=settings.GEMINI_IMAGE_GEN_MODEL
            )
            self._image_gen_available = True
        except Exception as exc:
            logger.warning(
                "Görüntü üretim modeli başlatılamadı (%s). "
                "Gemini 2.0 Flash fallback'e geçiliyor.",
                exc,
            )
            self._image_gen_available = False
            # Fallback: Gemini 2.0 Flash ile görüntü üretimi
            self.image_gen_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp-image-generation",
                generation_config=genai.GenerationConfig(
                    temperature=0.8,
                    response_modalities=["image", "text"],
                ),
            )

    # ------------------------------------------------------------------
    # 1. ÜRÜN ANALİZİ
    # ------------------------------------------------------------------

    def analyze_product(
        self,
        image_data: bytes,
        extra_context: Optional[str] = None,
    ) -> dict:
        """
        Ürün fotoğrafını analiz eder.

        Returns:
            {
              "product_name": str,
              "category": str,
              "colors": [...],
              "materials": [...],
              "style": str,
              "key_features": [...],
              "suggested_backgrounds": [...],
              "lighting_recommendation": str,
              "target_audience": str,
              "brand_tone": str
            }
        """
        image_data, mime_type = _load_and_validate_image(image_data)
        image_part = _image_to_part(image_data, mime_type)

        prompt = self._build_analysis_prompt(extra_context)

        logger.debug("Ürün analizi başlatılıyor...")
        response = self.vision_model.generate_content([prompt, image_part])

        if not response.text:
            raise RuntimeError("Gemini analiz yanıtı boş döndü.")

        import json  # noqa: PLC0415

        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            # Modelin JSON bloğunu ```json ... ``` içine sardığı durumlar
            cleaned = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(cleaned)

    @staticmethod
    def _build_analysis_prompt(extra_context: Optional[str]) -> str:
        base = """Sen profesyonel bir ürün fotoğrafçısı ve e-ticaret görsel uzmanısın.
Verilen ürün fotoğrafını ayrıntılı biçimde analiz et ve YALNIZCA aşağıdaki
JSON şemasına uygun bir yanıt döndür (başka metin ekleme):

{
  "product_name": "<tahmin edilen ürün adı>",
  "category": "<ürün kategorisi>",
  "colors": ["<renk1>", "<renk2>"],
  "materials": ["<malzeme1>"],
  "style": "<modern|minimalist|lüks|spor|klasik|...>",
  "key_features": ["<özellik1>", "<özellik2>"],
  "suggested_backgrounds": ["<arka plan önerisi 1>", "<arka plan önerisi 2>", "<arka plan önerisi 3>"],
  "lighting_recommendation": "<ışık önerisi>",
  "target_audience": "<hedef kitle>",
  "brand_tone": "<marka tonu>"
}"""
        if extra_context:
            base += f"\n\nEk bağlam: {extra_context}"
        return base

    # ------------------------------------------------------------------
    # 2. FOTOĞRAF ÇEKİM AÇISI PROMPT'LARI OLUŞTURMA
    # ------------------------------------------------------------------

    def generate_shot_prompts(
        self,
        analysis: dict,
        image_data: bytes,
    ) -> list[dict]:
        """
        Ürün analizine dayanarak 5 farklı profesyonel çekim açısı için
        görüntü üretim promptları oluşturur.

        Returns:
            [
              {"angle": "...", "prompt": "...", "negative_prompt": "..."},
              ...  (5 adet)
            ]
        """
        image_data, mime_type = _load_and_validate_image(image_data)
        image_part = _image_to_part(image_data, mime_type)

        prompt = self._build_shot_prompt_request(analysis)

        # Metin modeli ile prompt listesi üret (görüntüyü referans olarak ver)
        response = self.vision_model.generate_content(
            [prompt, image_part],
            generation_config=DESCRIPTION_GENERATION_CONFIG,
        )

        if not response.text:
            raise RuntimeError("Çekim prompt'ları üretilemedi.")

        import json  # noqa: PLC0415

        cleaned = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(cleaned)

    @staticmethod
    def _build_shot_prompt_request(analysis: dict) -> str:
        return f"""Sen uzman bir ürün fotoğrafçısı ve AI görüntü üretim prompt yazarısın.

Aşağıdaki ürün analizine göre, bu ürün için 5 farklı profesyonel çekim açısı belirle
ve her biri için bir görüntü üretim promptu oluştur.

Ürün Analizi:
{analysis}

Lütfen YALNIZCA aşağıdaki JSON dizisini döndür:
[
  {{
    "angle": "<çekim açısı adı (Türkçe)>",
    "description": "<bu açının amacı>",
    "prompt": "<İngilizce, detaylı görüntü üretim promptu - ürünü, arka planı, ışığı, atmosferi içermeli>",
    "negative_prompt": "<kaçınılacak unsurlar (İngilizce)>"
  }},
  ... (toplamda 5 eleman)
]

Çekim açısı önerileri (bunlardan seç veya uyarla):
1. Hero Shot — ürünü öne çıkaran ana tanıtım çekimi
2. Detail / Close-up — malzeme ve doku vurgusu
3. Lifestyle / Context — ürünün kullanım ortamında gösterimi
4. 45° Three-Quarter — klasik ürün kataloğu açısı
5. Flat Lay / Top-Down — minimalist üstten çekim"""

    # ------------------------------------------------------------------
    # 3. GÖRÜNTÜ ÜRETME
    # ------------------------------------------------------------------

    def generate_product_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        reference_image: Optional[bytes] = None,
        number_of_images: int = 1,
    ) -> list[bytes]:
        """
        Verilen prompt ile profesyonel ürün fotoğrafı üretir.

        Args:
            prompt: Görüntü üretim promptu
            negative_prompt: Kaçınılacak unsurlar
            reference_image: Referans ürün görseli (opsiyonel)
            number_of_images: Üretilecek görüntü sayısı (1-4)

        Returns:
            PNG formatında görüntü byte listesi
        """
        if self._image_gen_available:
            return self._generate_via_imagen(prompt, negative_prompt, number_of_images)
        return self._generate_via_gemini_flash(prompt, reference_image)

    def _generate_via_imagen(
        self,
        prompt: str,
        negative_prompt: str,
        number_of_images: int,
    ) -> list[bytes]:
        """Imagen 3 ile görüntü üretimi."""
        logger.debug("Imagen ile görüntü üretiliyor: %s...", prompt[:80])
        response = self.image_gen_model.generate_images(
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            number_of_images=number_of_images,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="dont_allow",
        )
        return [img._image_bytes for img in response.images]  # noqa: SLF001

    def _generate_via_gemini_flash(
        self,
        prompt: str,
        reference_image: Optional[bytes],
    ) -> list[bytes]:
        """Gemini 2.0 Flash ile görüntü üretimi (fallback)."""
        logger.debug("Gemini Flash ile görüntü üretiliyor...")
        parts = [prompt]
        if reference_image:
            ref_data, mime_type = _load_and_validate_image(reference_image)
            parts.append(_image_to_part(ref_data, mime_type))

        response = self.image_gen_model.generate_content(parts)
        images = []
        for part in response.parts:
            if part.inline_data and "image" in part.inline_data.mime_type:
                images.append(base64.b64decode(part.inline_data.data))
        if not images:
            raise RuntimeError("Görüntü üretimi başarısız: yanıtta görüntü yok.")
        return images

    # ------------------------------------------------------------------
    # 4. BAĞLANTI TESTİ
    # ------------------------------------------------------------------

    def health_check(self) -> dict:
        """API bağlantısını ve model erişimini test eder."""
        try:
            response = self.text_model.generate_content(
                "Merhaba! Yalnızca 'OK' yaz.",
                generation_config=genai.GenerationConfig(max_output_tokens=5),
            )
            return {
                "status": "healthy",
                "vision_model": settings.GEMINI_VISION_MODEL,
                "text_model": settings.GEMINI_TEXT_MODEL,
                "image_gen_model": settings.GEMINI_IMAGE_GEN_MODEL,
                "image_gen_available": self._image_gen_available,
                "test_response": response.text.strip(),
            }
        except Exception as exc:
            logger.error("Gemini health check başarısız: %s", exc)
            return {"status": "unhealthy", "error": str(exc)}
