"""Aplicación FastAPI principal."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import get_settings
from app.models import init_db, close_db
from app.routers import auth, dashboard, users, devices, profiles, dns, stats
from app.scheduler import init_scheduler, stop_scheduler
from app.services.mikrotik_client import MikroTikClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de startup y shutdown de la aplicación."""
    # Startup
    logger.info("Inicializando aplicación NAC...")
    db = await init_db()
    logger.info("Base de datos inicializada")

    # Inicializar scheduler
    settings = get_settings()
    try:
        scheduler = await init_scheduler(db, None)
        logger.info("Scheduler inicializado con tareas periódicas")
    except Exception as e:
        logger.warning(f"Error inicializando scheduler: {e}")

    yield

    # Shutdown
    logger.info("Cerrando conexiones...")
    try:
        await stop_scheduler()
    except:
        pass
    await close_db()


app = FastAPI(
    title="MikroTik NAC System",
    description="Network Access Control para PDVSA",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración
settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers API
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(dns.router, prefix="/api")
app.include_router(stats.router, prefix="/api")

# Health check
@app.get("/health")
async def health():
    """Health check del sistema."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
    }


# Archivos estáticos (frontend)
from pathlib import Path
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def root():
        """Sirve la página principal."""
        from fastapi.responses import FileResponse
        return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")
else:
    logger.warning(f"Directorio static no encontrado: {STATIC_DIR}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
