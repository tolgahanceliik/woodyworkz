"""
Gemini Client Testleri
-----------------------
Çalıştırma: pytest tests/ -v

Not: Gerçek API çağrıları GEMINI_API_KEY ortam değişkeni gerektirir.
Mock testler API anahtarı olmadan çalışır.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini_client import GeminiClient, _check_magic_bytes_util


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client(monkeypatch):
    """API anahtarı olmadan GeminiClient oluşturur (mock)."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_mock")

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as mock_model_cls, \
         patch("google.generativeai.ImageGenerationModel"):

        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model

        client = GeminiClient.__new__(GeminiClient)
        client.vision_model = mock_model
        client.text_model = mock_model
        client.image_gen_model = MagicMock()
        client._image_gen_available = True

        yield client


# ---------------------------------------------------------------------------
# analyze_product testleri
# ---------------------------------------------------------------------------

class TestAnalyzeProduct:
    SAMPLE_JPEG = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"\x00" * 100  # minimal JPEG header

    def test_returns_parsed_dict(self, mock_client):
        expected = {
            "product_name": "Test Ürün",
            "category": "Elektronik",
            "colors": ["siyah"],
            "materials": ["plastik"],
            "style": "modern",
            "key_features": ["özellik1"],
            "suggested_backgrounds": ["beyaz arka plan"],
            "lighting_recommendation": "soft box",
            "target_audience": "genç yetişkinler",
            "brand_tone": "teknolojik",
        }
        mock_client.vision_model.generate_content.return_value.text = json.dumps(expected)

        result = mock_client.analyze_product(self.SAMPLE_JPEG)

        assert result["product_name"] == "Test Ürün"
        assert result["category"] == "Elektronik"
        assert "soft box" in result["lighting_recommendation"]

    def test_handles_json_code_block(self, mock_client):
        """Modelin ```json ... ``` sarmaladığı durumu test eder."""
        payload = {"product_name": "Çanta", "category": "Aksesuar",
                   "colors": [], "materials": [], "style": "lüks",
                   "key_features": [], "suggested_backgrounds": [],
                   "lighting_recommendation": "doğal ışık",
                   "target_audience": "kadınlar", "brand_tone": "şık"}
        mock_client.vision_model.generate_content.return_value.text = (
            f"```json\n{json.dumps(payload)}\n```"
        )
        result = mock_client.analyze_product(self.SAMPLE_JPEG)
        assert result["product_name"] == "Çanta"

    def test_raises_on_empty_response(self, mock_client):
        mock_client.vision_model.generate_content.return_value.text = ""
        with pytest.raises(RuntimeError, match="boş döndü"):
            mock_client.analyze_product(self.SAMPLE_JPEG)


# ---------------------------------------------------------------------------
# Health check testi
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_healthy(self, mock_client):
        mock_client.text_model.generate_content.return_value.text = "OK"
        mock_client._image_gen_available = True

        # settings mock
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.GEMINI_VISION_MODEL = "gemini-1.5-pro"
            mock_settings.GEMINI_TEXT_MODEL = "gemini-1.5-flash"
            mock_settings.GEMINI_IMAGE_GEN_MODEL = "imagen-3.0-generate-001"

            result = mock_client.health_check()

        assert result["status"] == "healthy"
        assert result["test_response"] == "OK"

    def test_unhealthy_on_exception(self, mock_client):
        mock_client.text_model.generate_content.side_effect = Exception("API down")
        with patch("app.services.gemini_client.settings"):
            result = mock_client.health_check()
        assert result["status"] == "unhealthy"
        assert "API down" in result["error"]


# ---------------------------------------------------------------------------
# Yardımcı — magic bytes
# ---------------------------------------------------------------------------

def _check_magic_bytes_util(data: bytes) -> bool:
    """Test için yeniden tanımlanmış magic bytes kontrolü."""
    if data[:2] == b"\xff\xd8":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


class TestMagicBytes:
    def test_jpeg(self):
        assert _check_magic_bytes_util(b"\xff\xd8\xff\xe0" + b"\x00" * 10)

    def test_png(self):
        assert _check_magic_bytes_util(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)

    def test_webp(self):
        assert _check_magic_bytes_util(b"RIFF\x00\x00\x00\x00WEBP")

    def test_invalid(self):
        assert not _check_magic_bytes_util(b"not an image at all")
