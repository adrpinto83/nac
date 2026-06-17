"""Aplicación FastAPI principal - NAC System."""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from app.database import init_db
from app.routers import auth, users, devices, router_sync

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Splash page URL
SPLASH_PAGE_URL = "https://nac-production.up.railway.app/splash"

class CaptivePortalMiddleware(BaseHTTPMiddleware):
    """Middleware para detectar y redirigir clientes de captive portal"""
    async def dispatch(self, request: Request, call_next):
        # Si es una solicitud a una ruta conocida, dejar pasar
        safe_paths = ["/api", "/health", "/docs", "/redoc", "/openapi.json", "/static"]

        # Si NO es una ruta API/admin, probablemente sea un cliente captive portal
        if not any(request.url.path.startswith(path) for path in safe_paths):
            if request.url.path != "/" and request.url.path != "/splash":
                logger.info(f"Captive Portal Redirect: {request.client.host} → {request.url.path}")
                return RedirectResponse(url=SPLASH_PAGE_URL, status_code=302)

        response = await call_next(request)
        return response


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

# Captive Portal Middleware
app.add_middleware(CaptivePortalMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers primero
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(router_sync.router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "nac-system",
    }

# Endpoint de prueba
@app.get("/api/status")
async def status():
    """Estado del sistema."""
    return {
        "status": "running",
        "version": "1.0.0",
        "authentication": "enabled",
    }

# Servir frontend - AL FINAL PARA NO INTERFERIR
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    # Mount static files first
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Serve index.html en raíz (AFTER mounting static files)
    @app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
    async def root():
        """Página principal."""
        with open(str(STATIC_DIR / "index.html"), "r") as f:
            return f.read()

    # Serve splash page for public registration
    @app.api_route("/splash", methods=["GET", "HEAD"], response_class=HTMLResponse)
    async def splash():
        """Página de registro público (splash page)."""
        with open(str(STATIC_DIR / "splash.html"), "r") as f:
            return f.read()

logger.info("🚀 Aplicación NAC iniciada correctamente")
