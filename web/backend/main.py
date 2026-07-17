"""
main.py — FastAPI backend for the NEF→JPG online converter.

Endpoints:
  GET  /health   → Liveness check (used by Render + frontend warm-up)
  POST /convert  → Converts uploaded RAW file, returns JPEG bytes
"""

import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from converter import ConversionError, MAX_FILE_SIZE, convert_raw_to_jpeg

# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("nef2jpg")

app = FastAPI(
    title="NEF → JPG API",
    description="Convert RAW camera files to JPEG via rawpy + Pillow.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow any origin so the Vercel frontend can reach us
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Original-Name"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    """Liveness check — also used by the frontend to wake up the server."""
    return {"status": "ok", "service": "nef2jpg-api"}


@app.post("/convert")
async def convert(
    file: UploadFile = File(..., description="RAW image file (NEF, CR2, ARW, …)"),
    quality: int = Form(90, ge=50, le=100, description="JPEG quality 50–100"),
    max_dimension: int = Form(0, ge=0, description="Max px on longest edge (0 = original)"),
):
    """
    Accept a RAW file upload and return the converted JPEG.

    - **file**: multipart file field
    - **quality**: integer 50–100 (default 90)
    - **max_dimension**: 0 means keep original size
    """
    filename = file.filename or "photo.nef"
    log.info("Received: %s  quality=%d  max_dim=%d", filename, quality, max_dimension)

    # Read with size limit
    data = await file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    try:
        jpeg_bytes = convert_raw_to_jpeg(
            data=data,
            filename=filename,
            quality=quality,
            max_dimension=max_dimension if max_dimension > 0 else None,
        )
    except ConversionError as e:
        log.warning("Conversion failed: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log.error("Unexpected error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

    stem = Path(filename).stem
    output_name = f"{stem}.jpg"
    log.info("Done: %s  size=%d KB", output_name, len(jpeg_bytes) // 1024)

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{output_name}"',
            "X-Original-Name": output_name,
            "Cache-Control": "no-store",
        },
    )


# ---------------------------------------------------------------------------
# Generic error handler — always return JSON, never HTML
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})
