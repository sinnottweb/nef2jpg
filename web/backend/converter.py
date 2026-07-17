"""
converter.py — Core RAW-to-JPEG logic for the web backend.
Accepts raw bytes, returns JPEG bytes.
"""

import io
import os
import tempfile
from pathlib import Path
from typing import Optional


SUPPORTED_EXTENSIONS = {".nef", ".cr2", ".cr3", ".arw", ".dng", ".raf", ".rw2", ".orf", ".pef"}
MAX_FILE_SIZE = 80 * 1024 * 1024  # 80 MB


class ConversionError(Exception):
    pass


def convert_raw_to_jpeg(
    data: bytes,
    filename: str,
    quality: int = 90,
    max_dimension: Optional[int] = None,
) -> bytes:
    """
    Convert RAW image bytes to JPEG bytes.

    Parameters
    ----------
    data          : Raw file content as bytes.
    filename      : Original filename (used to validate extension).
    quality       : JPEG quality 50–100.
    max_dimension : If set, resize so longest edge ≤ max_dimension px.

    Returns
    -------
    JPEG image as bytes.

    Raises
    ------
    ConversionError : On any known failure.
    """
    import rawpy
    import numpy as np
    from PIL import Image

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ConversionError(
            f"Formato '{ext}' no soportado. "
            f"Formatos válidos: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if len(data) > MAX_FILE_SIZE:
        raise ConversionError(
            f"Archivo demasiado grande ({len(data) // (1024*1024)} MB). Máximo: 80 MB."
        )

    # Write to a temp file — rawpy needs a real file path
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(data)

        try:
            with rawpy.imread(tmp_path) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=False,
                    no_auto_bright=False,
                    output_bps=8,
                    demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
                )
        except rawpy.LibRawFileUnsupportedError:
            raise ConversionError("Formato RAW no reconocido o no soportado por LibRaw.")
        except rawpy.LibRawIOError:
            raise ConversionError("El archivo está corrupto o incompleto.")
        except Exception as e:
            raise ConversionError(f"Error al decodificar el RAW: {e}")

        image = Image.fromarray(rgb)

        if max_dimension and max_dimension > 0:
            image = _resize(image, max_dimension)

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        buf.seek(0)
        return buf.read()

    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _resize(image, max_dim: int):
    """Resize so the longest edge ≤ max_dim, preserving aspect ratio."""
    from PIL import Image as PILImage
    w, h = image.size
    if max(w, h) <= max_dim:
        return image
    scale = max_dim / max(w, h)
    return image.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
