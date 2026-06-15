"""Aplicación FastAPI principal - NAC System."""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación
app = FastAPI(
    title="MikroTik NAC System",
    description="Network Access Control",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "nac-system",
    }

# Servir frontend
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def root():
        """Página principal."""
        return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")
else:
    @app.get("/")
    async def root():
        """Página principal (alternativa)."""
        return {
            "message": "NAC System running",
            "docs": "/docs"
        }

# Endpoint de prueba
@app.get("/api/status")
async def status():
    """Estado del sistema."""
    return {
        "status": "running",
        "version": "1.0.0",
    }

logger.info("🚀 Aplicación NAC iniciada correctamente")
