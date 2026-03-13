"""
Prompt Builder
--------------
WoodAnalysis + kullanıcı ortam tercihi (stüdyo, doğa, ev vb.) →
Gemini Image Generation için 5 farklı açıda detaylı İngilizce prompt.

Her çekim sabit bir kompozisyon şablonuna sahiptir:
  1. Ön Görünüm      (Front View)
  2. Yan Görünüm     (Side View)
  3. Üstten Görünüm  (Top-Down / Flat Lay)
  4. 45° Açı         (Three-Quarter)
  5. Yakın Detay     (Close-Up Detail)

Kullanım:
    builder = PromptBuilder()
    shots = builder.build(
        analysis=wood_analysis,      # GeminiService çıktısı
        environment="studio",        # Kullanıcı seçimi
        style_override=None,         # Opsiyonel stil geçersiz kılma
    )
    # shots → list[ShotBundle]  (prompt + negative_prompt + meta)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.models.schemas import WoodAnalysis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ortam tipleri
# ---------------------------------------------------------------------------

class ShootEnvironment(str, Enum):
    """Kullanıcının seçeceği çekim ortamı."""
    STUDIO       = "studio"        # Sade, arka fon kağıdı / seamless
    NATURE       = "nature"        # Orman, açık hava, doğal ışık
    HOME         = "home"          # Ev içi, oturma odası / mutfak
    WORKSHOP     = "workshop"      # Atölye, ahşap talaş, ham yüzeyler
    MINIMALIST   = "minimalist"    # Beyaz / beton, hiçbir dikkat dağıtıcı unsur
    LUXURY       = "luxury"        # Mermer, deri, altın aksesuar, soft light
    OUTDOOR_CAFE = "outdoor_cafe"  # Taş döşeme, bitki, doğal doku


# ---------------------------------------------------------------------------
# Ortam promptları (temel arka plan + ışık bağlamı)
# ---------------------------------------------------------------------------

_ENV_CONTEXT: dict[ShootEnvironment, dict] = {
    ShootEnvironment.STUDIO: {
        "background": "seamless white paper backdrop, professional photography studio",
        "lighting": "softbox studio lighting, controlled diffused light, no harsh shadows",
        "atmosphere": "clean, crisp, commercial product photography",
    },
    ShootEnvironment.NATURE: {
        "background": "lush forest floor, dappled sunlight through tree canopy, moss and ferns",
        "lighting": "natural golden hour sunlight, soft directional light",
        "atmosphere": "organic, earthy, back-to-nature feel",
    },
    ShootEnvironment.HOME: {
        "background": "cozy living room interior, warm ambient light, linen sofa nearby",
        "lighting": "warm indoor ambient light, window sidelight",
        "atmosphere": "lifestyle, inviting, homey warmth",
    },
    ShootEnvironment.WORKSHOP: {
        "background": "rustic woodworking workshop, scattered wood shavings, workbench surface",
        "lighting": "industrial pendant lamp, dramatic directional light",
        "atmosphere": "artisanal, raw craftsmanship, honest materials",
    },
    ShootEnvironment.MINIMALIST: {
        "background": "pure white or light grey concrete surface, no distractions",
        "lighting": "even diffused light, subtle shadows, Scandinavian minimalism",
        "atmosphere": "clean, architectural, breathing room, whitespace",
    },
    ShootEnvironment.LUXURY: {
        "background": "Carrara marble surface, deep shadow, rich gold and velvet accents",
        "lighting": "dramatic chiaroscuro, spotlight accent, premium mood",
        "atmosphere": "high-end, opulent, luxury product editorial",
    },
    ShootEnvironment.OUTDOOR_CAFE: {
        "background": "sunlit stone terrace, potted Mediterranean plants, wrought-iron chair",
        "lighting": "bright afternoon sun, natural warm tones",
        "atmosphere": "relaxed outdoor lifestyle, alfresco, Mediterranean vibe",
    },
}

# ---------------------------------------------------------------------------
# 5 çekim açısı tanımları
# ---------------------------------------------------------------------------

@dataclass
class AngleDefinition:
    """Bir çekim açısının sabit kompozisyon kuralları."""
    name_tr: str           # Türkçe görünen ad
    name_en: str           # İngilizce teknik ad
    camera_position: str   # Kamera konumu tanımı
    focal_emphasis: str    # Bu açıda neye odaklanılır
    lens_hint: str         # Öneri lens / focal length
    composition_rules: str # Kompozisyon kuralları


_ANGLE_DEFS: list[AngleDefinition] = [
    AngleDefinition(
        name_tr="Ön Görünüm",
        name_en="Front View",
        camera_position="camera positioned directly in front, eye-level, centered",
        focal_emphasis="overall silhouette, proportions, front face symmetry",
        lens_hint="50mm or 85mm equivalent, slight telephoto compression",
        composition_rules="product centered, rule of thirds horizon, ample negative space on sides",
    ),
    AngleDefinition(
        name_tr="Yan Görünüm",
        name_en="Side View",
        camera_position="camera positioned 90° to the side, eye-level or slightly elevated",
        focal_emphasis="profile, depth, joinery details, thickness of wood",
        lens_hint="85mm equivalent, shallow depth of field",
        composition_rules="product occupies left or right third, leading lines of grain visible",
    ),
    AngleDefinition(
        name_tr="Üstten Görünüm",
        name_en="Top-Down / Flat Lay",
        camera_position="camera directly overhead, 90° nadir angle",
        focal_emphasis="surface pattern, grain texture, surface area, flat composition",
        lens_hint="24-35mm equivalent, wide enough to show full surface",
        composition_rules="centered or off-center with intentional negative space, minimalist styling",
    ),
    AngleDefinition(
        name_tr="45° Açı",
        name_en="Three-Quarter View",
        camera_position="camera at 45° horizontal angle, slightly elevated (30-45° vertical)",
        focal_emphasis="three-dimensional form, depth, volume, craftsmanship showcase",
        lens_hint="50mm equivalent, medium depth of field",
        composition_rules=(
            "product fills 60-70% of frame, diagonal leading lines, "
            "front and one side visible simultaneously"
        ),
    ),
    AngleDefinition(
        name_tr="Yakın Detay",
        name_en="Close-Up Detail",
        camera_position="macro or tight crop, camera very close to a specific feature",
        focal_emphasis="wood grain texture, finish quality, joinery craftsmanship, material authenticity",
        lens_hint="macro lens or 100mm, very shallow depth of field (f/2.8 or wider)",
        composition_rules=(
            "extreme bokeh background, sharp focus on one defining detail, "
            "fills entire frame with texture"
        ),
    ),
]


# ---------------------------------------------------------------------------
# Çıktı modeli
# ---------------------------------------------------------------------------

@dataclass
class ShotBundle:
    """Tek bir çekim açısı için tam prompt paketi."""
    index: int                  # 1-5
    angle_tr: str               # Türkçe ad
    angle_en: str               # İngilizce teknik ad
    environment: str            # Seçilen ortam
    prompt: str                 # Tam İngilizce üretim promptu
    negative_prompt: str        # Kaçınılacak unsurlar
    camera_notes: str           # Fotoğrafçı için kamera/lens notu
    focal_emphasis: str         # Ne vurgulanıyor


# ---------------------------------------------------------------------------
# Ana sınıf
# ---------------------------------------------------------------------------

class PromptBuilder:
    """
    WoodAnalysis + ortam seçimi → 5 çekim açısı prompt listesi.

    Her prompt şu katmanlardan oluşur:
      [ürün kimliği] + [malzeme/doku] + [ortam/arka plan] +
      [ışık] + [açı/kompozisyon] + [kalite direktifleri]
    """

    # Tüm promptlara eklenen evrensel kalite direktifleri
    _QUALITY_SUFFIX = (
        "ultra-detailed, photorealistic, 8K resolution, "
        "professional commercial product photography, "
        "shot on Phase One IQ4, tack-sharp focus on product, "
        "color-graded, magazine-quality"
    )

    # Tüm negative prompt'lara eklenen evrensel kaçınılacaklar
    _UNIVERSAL_NEGATIVES = (
        "cartoon, illustration, painting, 3D render, CGI, low quality, "
        "blurry, grainy, overexposed, underexposed, watermark, text, "
        "logo, people, hands, plastic look, artificial texture, "
        "distorted proportions, cropped product, missing parts"
    )

    def build(
        self,
        analysis: WoodAnalysis,
        environment: str | ShootEnvironment = ShootEnvironment.STUDIO,
        style_override: Optional[str] = None,
    ) -> list[ShotBundle]:
        """
        5 çekim açısı için tam prompt listesi üretir.

        Args:
            analysis:       GeminiService.analyze_product_images() çıktısı.
            environment:    Kullanıcının seçtiği ortam (str veya ShootEnvironment).
            style_override: Analiz'den gelen stili geçersiz kılmak isterse
                            kullanıcı buradan verir (örn: "industrial").

        Returns:
            list[ShotBundle]  — 5 elemanlı, index 1-5.
        """
        env = self._resolve_env(environment)
        env_ctx = _ENV_CONTEXT[env]
        style = style_override or analysis.style

        # Ürün kimliği cümlesi — tüm promptlarda ortak
        product_core = self._build_product_core(analysis, style)

        # Ortam bağlamı cümlesi
        env_phrase = (
            f"{env_ctx['background']}, {env_ctx['lighting']}, "
            f"{env_ctx['atmosphere']}"
        )

        # Ürüne özgü negatif promptlar + evrensel
        product_negatives = ", ".join(analysis.negative_keywords) if analysis.negative_keywords else ""
        full_negative = (
            f"{product_negatives}, {self._UNIVERSAL_NEGATIVES}"
            if product_negatives
            else self._UNIVERSAL_NEGATIVES
        )

        shots: list[ShotBundle] = []
        for idx, angle in enumerate(_ANGLE_DEFS, start=1):
            prompt = self._compose_prompt(
                product_core=product_core,
                env_phrase=env_phrase,
                angle=angle,
                analysis=analysis,
            )
            shots.append(
                ShotBundle(
                    index=idx,
                    angle_tr=angle.name_tr,
                    angle_en=angle.name_en,
                    environment=env.value,
                    prompt=prompt,
                    negative_prompt=full_negative,
                    camera_notes=f"{angle.lens_hint} | {angle.camera_position}",
                    focal_emphasis=angle.focal_emphasis,
                )
            )
            logger.debug("Prompt #%d oluşturuldu: %s", idx, angle.name_en)

        return shots

    # ------------------------------------------------------------------
    # Dahili yardımcılar
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_env(env: str | ShootEnvironment) -> ShootEnvironment:
        if isinstance(env, ShootEnvironment):
            return env
        try:
            return ShootEnvironment(env.lower())
        except ValueError:
            logger.warning("Bilinmeyen ortam '%s', 'studio' kullanılıyor.", env)
            return ShootEnvironment.STUDIO

    @staticmethod
    def _build_product_core(analysis: WoodAnalysis, style: str) -> str:
        """
        Ürünün ne olduğunu, malzemesini ve görsel özelliklerini
        tek bir İngilizce cümlede özetler.
        Tüm açı promptlarında ortak temel olarak kullanılır.
        """
        # Ağaç türü
        wood = analysis.wood_species
        wood_str = f"solid {wood} wood" if wood != "unknown" else "solid hardwood"

        # Renk
        color_parts = [analysis.color.primary]
        if analysis.color.secondary:
            color_parts.append(f"with {', '.join(analysis.color.secondary[:2])} secondary tones")
        color_str = " ".join(color_parts)

        # Damar
        grain = analysis.grain
        grain_str = f"{grain.visibility} {grain.pattern} grain pattern"

        # Yüzey işlem
        finish = analysis.finish
        finish_str = f"{finish.type} finish, {finish.sheen} sheen, {finish.texture_feel} surface"

        # Ayırt edici özellikler
        features = analysis.distinctive_features[:3]
        feature_str = (", ".join(features) + ", ") if features else ""

        # Prompt keyword'leri (en fazla 6)
        kw_str = ", ".join(analysis.prompt_keywords[:6])

        return (
            f"{analysis.product_name}, {wood_str}, "
            f"{color_str}, {grain_str}, "
            f"{feature_str}"
            f"{finish_str}, "
            f"{analysis.craftsmanship.replace('_', ' ')}, "
            f"{style} style, "
            f"{kw_str}"
        )

    def _compose_prompt(
        self,
        product_core: str,
        env_phrase: str,
        angle: AngleDefinition,
        analysis: WoodAnalysis,
    ) -> str:
        """
        Katmanları birleştirerek tek bir prompt cümlesi oluşturur.

        Yapı:
          SUBJECT + ANGLE + ENVIRONMENT + COMPOSITION + QUALITY
        """
        # Açıya özel vurgu
        if angle.name_en == "Close-Up Detail":
            # Yakın çekim için en güçlü malzeme detayı öne çıkar
            grain_detail = analysis.grain.description or "rich wood grain texture"
            angle_phrase = (
                f"extreme close-up macro photograph focusing on {grain_detail}, "
                f"{analysis.finish.texture_feel} surface texture visible at microscopic level, "
                f"ultra-shallow depth of field, {angle.composition_rules}"
            )
        elif angle.name_en == "Top-Down / Flat Lay":
            # Üstten çekim için yüzey kompozisyonu
            extra_items = self._flat_lay_props(analysis)
            angle_phrase = (
                f"{angle.camera_position}, "
                f"{angle.composition_rules}, "
                f"flat lay composition, {extra_items}"
            )
        else:
            angle_phrase = (
                f"{angle.camera_position}, "
                f"{angle.focal_emphasis}, "
                f"{angle.composition_rules}"
            )

        return (
            f"{product_core}, "
            f"{angle_phrase}, "
            f"{env_phrase}, "
            f"{self._QUALITY_SUFFIX}"
        )

    @staticmethod
    def _flat_lay_props(analysis: WoodAnalysis) -> str:
        """
        Üstten çekim için ürünle uyumlu styling öğeleri önerir.
        Ahşap türüne ve stile göre farklılaşır.
        """
        style_props: dict[str, str] = {
            "rustic":       "dried botanical sprigs, linen cloth, raw stone beside it",
            "scandinavian": "single green leaf, white ceramic cup, clean linen",
            "industrial":   "metal hex bolts, worn leather patch, dark felt",
            "modern":       "single geometric object, minimal white surface",
            "traditional":  "small brass candle holder, dried flowers, aged paper",
            "mid_century":  "retro ceramic vase, warm amber glass, clean backdrop",
            "wabi_sabi":    "irregular pebble, washi paper, asymmetric moss patch",
            "bohemian":     "macramé coaster, dried pampas grass, warm terracotta",
            "minimalist":   "single smooth stone, abundant negative space",
            "farmhouse":    "sprig of eucalyptus, rough linen, vintage key",
            "japandi":      "single white blossom, bamboo chopstick, muted grey linen",
        }
        return style_props.get(
            analysis.style,
            "simple complementary natural props, curated minimal styling",
        )

    # ------------------------------------------------------------------
    # Yardımcı: ShotBundle → dict (API yanıtı için)
    # ------------------------------------------------------------------

    @staticmethod
    def bundles_to_dict(bundles: list[ShotBundle]) -> list[dict]:
        """ShotBundle listesini JSON-serializable dict listesine çevirir."""
        return [
            {
                "index": b.index,
                "angle": b.angle_tr,
                "angle_en": b.angle_en,
                "environment": b.environment,
                "prompt": b.prompt,
                "negative_prompt": b.negative_prompt,
                "camera_notes": b.camera_notes,
                "focal_emphasis": b.focal_emphasis,
            }
            for b in bundles
        ]
