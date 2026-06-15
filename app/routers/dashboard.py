"""Router de dashboard."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import get_db, Database
from app.services import DashboardService
from app.schemas import DashboardMetrics, TopDevicesByTraffic, Alert
from app.dependencies import get_current_user, get_router_client
from routeros.client import RouterOSClient

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Obtiene métricas del dashboard en tiempo real."""
    try:
        service = DashboardService(db, router)
        metrics = await service.get_metrics()
        return DashboardMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/top-devices", response_model=list[TopDevicesByTraffic])
async def get_top_devices(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Obtiene top dispositivos por tráfico."""
    try:
        service = DashboardService(db, router)
        devices = await service.get_top_devices(limit)
        return [TopDevicesByTraffic(**d) for d in devices]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/alerts", response_model=list[Alert])
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Obtiene alertas del sistema."""
    try:
        service = DashboardService(db, router)
        alerts = await service.get_alerts()
        return [Alert(**a) for a in alerts]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/network-stats")
async def get_network_stats(
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
    router: RouterOSClient = Depends(get_router_client),
):
    """Obtiene estadísticas de la red."""
    try:
        service = DashboardService(db, router)
        stats = await service.get_network_stats(hours)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
