"""Aplicación FastAPI principal - NAC System."""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
from app.routers import auth, users, devices

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events (startup/shutdown)."""
    # Startup
    logger.info("Inicializando base de datos...")
    await init_db()
    logger.info("Base de datos inicializada")
    yield
    # Shutdown
    logger.info("Cerrando aplicación...")


# Crear aplicación
app = FastAPI(
    title="MikroTik NAC System",
    description="Network Access Control",
    version="1.0.0",
    lifespan=lifespan,
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

# Servir frontend - DEBE SER ANTES DE ROUTERS
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Serve index.html
    @app.get("/", response_class=FileResponse)
    async def root():
        """Página principal."""
        return FileResponse(str(STATIC_DIR / "index.html"))

# Routers - DESPUÉS DE STATIC
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(devices.router, prefix="/api")

# Endpoint de prueba
@app.get("/api/status")
async def status():
    """Estado del sistema."""
    return {
        "status": "running",
        "version": "1.0.0",
        "authentication": "enabled",
    }

logger.info("🚀 Aplicación NAC iniciada correctamente")
