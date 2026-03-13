"""
Görüntü Yardımcı Fonksiyonları
--------------------------------
Yükleme doğrulama, boyutlandırma ve kaydetme.
"""

from pathlib import Path

from fastapi import HTTPException, status


def validate_image(
    data: bytes,
    content_type: str,
    max_size_mb: int = 10,
    allowed_types: list[str] | None = None,
) -> None:
    """
    Yüklenen görüntüyü doğrular.
    Hatalıysa HTTPException fırlatır.
    """
    allowed = allowed_types or ["image/jpeg", "image/png", "image/webp"]

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Görüntü verisi boş.",
        )

    # MIME türü kontrolü
    if content_type and content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Desteklenmeyen dosya türü: {content_type}. İzin verilenler: {allowed}",
        )

    # Boyut kontrolü
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Dosya boyutu ({size_mb:.1f} MB) izin verilen sınırı ({max_size_mb} MB) aşıyor.",
        )

    # Magic bytes kontrolü (temel)
    if not _check_magic_bytes(data):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Dosya içeriği desteklenen bir görüntü formatı değil.",
        )


def _check_magic_bytes(data: bytes) -> bool:
    """JPEG, PNG veya WEBP magic bytes kontrolü."""
    if data[:2] == b"\xff\xd8":          # JPEG
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n": # PNG
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":  # WEBP
        return True
    return False


def save_image_bytes(data: bytes, path: Path) -> None:
    """Görüntü byte'larını dosyaya kaydeder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
