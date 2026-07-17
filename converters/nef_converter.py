"""
NEF to JPG Converter — Core conversion logic.
Uses rawpy (LibRaw) for RAW decoding and Pillow for post-processing.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Callable

import rawpy
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class ConversionError(Exception):
    """Raised when a conversion fails for a known reason."""
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_nef_to_jpg(
    input_path: str,
    output_path: str,
    quality: int = 90,
    max_dimension: Optional[int] = None,
    overwrite: bool = True,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Convert a single .NEF (or any LibRaw-supported RAW) file to JPEG.

    Parameters
    ----------
    input_path     : Path to the source RAW file.
    output_path    : Desired output .jpg path.
    quality        : JPEG quality 50–100.
    max_dimension  : If set, resize so the longest edge ≤ max_dimension (px).
    overwrite      : Whether to overwrite an existing output file.
    progress_callback : Optional callable(float 0-1) for progress updates.

    Returns
    -------
    (True, None)          on success
    (False, error_message) on failure
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)

        # --- Validations ---
        if not input_path.exists():
            raise ConversionError(f"Archivo no encontrado: {input_path.name}")

        if not os.access(input_path, os.R_OK):
            raise ConversionError(f"Sin permiso de lectura: {input_path.name}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not overwrite and output_path.exists():
            raise ConversionError(f"El archivo ya existe: {output_path.name}")

        # Check free space (rough estimate: 50 MB minimum)
        free = shutil.disk_usage(output_path.parent).free
        if free < 50 * 1024 * 1024:
            raise ConversionError("Espacio insuficiente en disco.")

        # --- RAW decoding ---
        if progress_callback:
            progress_callback(0.1)

        try:
            with rawpy.imread(str(input_path)) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=False,
                    no_auto_bright=False,
                    output_bps=8,
                    demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
                    bright=1.0,
                )
        except rawpy.LibRawFileUnsupportedError:
            raise ConversionError(f"Formato RAW no soportado: {input_path.name}")
        except rawpy.LibRawIOError:
            raise ConversionError(f"Archivo corrupto o incompleto: {input_path.name}")
        except Exception as e:
            raise ConversionError(f"Error decodificando RAW: {e}")

        if progress_callback:
            progress_callback(0.6)

        # --- Image processing ---
        image = Image.fromarray(rgb)

        if max_dimension and max_dimension > 0:
            image = _resize_image(image, max_dimension)

        if progress_callback:
            progress_callback(0.85)

        # --- Save JPEG ---
        try:
            image.save(
                str(output_path),
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
        except PermissionError:
            raise ConversionError(f"Sin permiso de escritura en: {output_path.parent}")
        except OSError as e:
            raise ConversionError(f"Error al guardar: {e}")

        if progress_callback:
            progress_callback(1.0)

        return True, None

    except ConversionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error inesperado: {e}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resize_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize image so the longest edge is ≤ max_dimension, preserving ratio."""
    w, h = image.size
    if max(w, h) <= max_dimension:
        return image

    if w >= h:
        new_w = max_dimension
        new_h = int(h * max_dimension / w)
    else:
        new_h = max_dimension
        new_w = int(w * max_dimension / h)

    return image.resize((new_w, new_h), Image.LANCZOS)


def get_output_path(input_path: str, output_dir: str) -> str:
    """Build the output .jpg path given an input file and output directory."""
    stem = Path(input_path).stem
    return str(Path(output_dir) / f"{stem}.jpg")


def is_valid_raw(path: str) -> bool:
    """Return True if the file extension is a known RAW format."""
    SUPPORTED = {".nef", ".cr2", ".cr3", ".arw", ".dng", ".raf", ".rw2"}
    return Path(path).suffix.lower() in SUPPORTED
