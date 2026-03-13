"""
GeminiService + PromptBuilder Testleri
----------------------------------------
Çalıştırma: pytest tests/test_gemini_service.py -v
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import WoodAnalysis, WoodGrain, WoodFinish, ColorProfile
from app.services.prompt_builder import PromptBuilder, ShootEnvironment, ShotBundle


# ---------------------------------------------------------------------------
# Sabit test verisi — WoodAnalysis nesnesi
# ---------------------------------------------------------------------------

SAMPLE_ANALYSIS = WoodAnalysis(
    product_name="Ceviz Yemek Masası",
    product_type="dining_table",
    use_case="functional",
    environment="indoor",
    wood_species="walnut",
    wood_species_confidence="high",
    wood_species_alternatives=["oak", "ash"],
    grain=WoodGrain(
        pattern="straight",
        visibility="prominent",
        description="Rich dark brown straight grain with occasional wavy figuring",
    ),
    finish=WoodFinish(
        type="oiled",
        sheen="satin",
        texture_feel="smooth",
    ),
    color=ColorProfile(
        primary="warm dark brown",
        secondary=["honey blonde sapwood streak"],
        undertone="warm",
        hex_estimate="#5C3D1E",
    ),
    style="mid_century",
    craftsmanship="handmade_artisan",
    joinery_details=["mortise_tenon", "butterfly_key"],
    distinctive_features=["live_edge", "sapwood_streak", "natural_knots"],
    size_estimate="large (>100cm), dining table approximately 180x90cm",
    prompt_keywords=[
        "solid walnut wood",
        "live edge slab",
        "hand-oiled finish",
        "visible wood grain",
        "natural edge",
        "artisan crafted",
        "mid-century modern",
        "warm brown tones",
    ],
    negative_keywords=["plastic", "laminate", "MDF", "veneer", "artificial grain"],
    lighting_recommendation="Warm directional sidelight at 45°, slight fill from opposite side",
    suggested_backgrounds=[
        "warm white seamless studio backdrop",
        "natural oak hardwood floor",
        "concrete loft interior",
    ],
    images_analyzed=2,
    analysis_notes=None,
)


# ---------------------------------------------------------------------------
# WoodAnalysis şema testleri
# ---------------------------------------------------------------------------

class TestWoodAnalysisSchema:
    def test_valid_model_instantiation(self):
        assert SAMPLE_ANALYSIS.product_name == "Ceviz Yemek Masası"
        assert SAMPLE_ANALYSIS.wood_species == "walnut"
        assert len(SAMPLE_ANALYSIS.prompt_keywords) >= 5

    def test_grain_nested_model(self):
        assert SAMPLE_ANALYSIS.grain.pattern == "straight"
        assert SAMPLE_ANALYSIS.grain.visibility == "prominent"

    def test_finish_nested_model(self):
        assert SAMPLE_ANALYSIS.finish.type == "oiled"
        assert SAMPLE_ANALYSIS.finish.sheen == "satin"

    def test_color_nested_model(self):
        assert SAMPLE_ANALYSIS.color.undertone == "warm"
        assert SAMPLE_ANALYSIS.color.hex_estimate == "#5C3D1E"

    def test_images_analyzed_bounds(self):
        with pytest.raises(Exception):
            SAMPLE_ANALYSIS.model_copy(update={"images_analyzed": 0})
        with pytest.raises(Exception):
            SAMPLE_ANALYSIS.model_copy(update={"images_analyzed": 5})


# ---------------------------------------------------------------------------
# GeminiService testleri (mock)
# ---------------------------------------------------------------------------

class TestGeminiService:
    MINIMAL_JPEG = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"\x00" * 200

    def _make_service(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as mock_cls:
            mock_model = MagicMock()
            mock_cls.return_value = mock_model
            from app.services.gemini_service import GeminiService
            svc = GeminiService.__new__(GeminiService)
            svc._model = mock_model
            return svc

    def test_rejects_empty_list(self, monkeypatch):
        from app.services.gemini_service import GeminiService
        svc = self._make_service(monkeypatch)
        with pytest.raises(ValueError, match="En az 1"):
            svc.analyze_product_images([])

    def test_rejects_too_many_images(self, monkeypatch):
        from app.services.gemini_service import GeminiService
        svc = self._make_service(monkeypatch)
        with pytest.raises(ValueError, match="4"):
            svc.analyze_product_images([self.MINIMAL_JPEG] * 5)

    def test_rejects_empty_image_bytes(self, monkeypatch):
        from app.services.gemini_service import GeminiService
        svc = self._make_service(monkeypatch)
        with pytest.raises(ValueError, match="boş"):
            svc.analyze_product_images([b""])

    def test_raises_on_empty_api_response(self, monkeypatch):
        from app.services.gemini_service import GeminiService
        svc = self._make_service(monkeypatch)
        svc._model.generate_content.return_value.text = ""
        with pytest.raises(RuntimeError, match="boş yanıt"):
            svc.analyze_product_images([self.MINIMAL_JPEG])

    def test_parse_response_cleans_markdown(self):
        from app.services.gemini_service import GeminiService
        payload = {"product_name": "Test"}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        result = GeminiService._parse_response(wrapped)
        assert result["product_name"] == "Test"

    def test_parse_response_extracts_embedded_json(self):
        from app.services.gemini_service import GeminiService
        payload = {"product_name": "Kase"}
        text = f"Sure, here it is:\n{json.dumps(payload)}\nDone."
        result = GeminiService._parse_response(text)
        assert result["product_name"] == "Kase"


# ---------------------------------------------------------------------------
# PromptBuilder testleri
# ---------------------------------------------------------------------------

class TestPromptBuilder:
    def test_returns_five_shots(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="studio")
        assert len(shots) == 5

    def test_shot_indices_are_1_to_5(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="studio")
        assert [s.index for s in shots] == [1, 2, 3, 4, 5]

    def test_angle_names_turkish(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS)
        names_tr = [s.angle_tr for s in shots]
        assert "Ön Görünüm" in names_tr
        assert "Yan Görünüm" in names_tr
        assert "Üstten Görünüm" in names_tr
        assert "45° Açı" in names_tr
        assert "Yakın Detay" in names_tr

    def test_all_prompts_contain_product_name(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="studio")
        for shot in shots:
            assert "walnut" in shot.prompt.lower() or "Ceviz" in shot.prompt

    def test_close_up_contains_grain(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="studio")
        close_up = next(s for s in shots if s.angle_en == "Close-Up Detail")
        assert "grain" in close_up.prompt.lower() or "texture" in close_up.prompt.lower()

    def test_top_down_contains_flat_lay(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="studio")
        top_down = next(s for s in shots if s.angle_en == "Top-Down / Flat Lay")
        assert "flat lay" in top_down.prompt.lower() or "overhead" in top_down.prompt.lower()

    def test_negative_prompt_contains_plastic(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS)
        for shot in shots:
            assert "plastic" in shot.negative_prompt.lower()

    def test_environment_nature_appears_in_prompt(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="nature")
        for shot in shots:
            assert "forest" in shot.prompt.lower() or "sunlight" in shot.prompt.lower()

    def test_unknown_environment_falls_back_to_studio(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment="spaceship")  # geçersiz
        assert shots[0].environment == "studio"

    def test_style_override(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, style_override="industrial")
        assert any("industrial" in s.prompt.lower() for s in shots)

    def test_bundles_to_dict_structure(self):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS)
        dicts = PromptBuilder.bundles_to_dict(shots)
        assert len(dicts) == 5
        required_keys = {"index", "angle", "angle_en", "environment", "prompt", "negative_prompt"}
        for d in dicts:
            assert required_keys.issubset(d.keys())

    @pytest.mark.parametrize("env", list(ShootEnvironment))
    def test_all_environments_produce_valid_prompts(self, env):
        builder = PromptBuilder()
        shots = builder.build(SAMPLE_ANALYSIS, environment=env)
        assert len(shots) == 5
        for shot in shots:
            assert len(shot.prompt) > 100  # boş/çok kısa değil
            assert isinstance(shot, ShotBundle)
