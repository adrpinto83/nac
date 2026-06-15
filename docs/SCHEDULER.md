# Scheduler - Tareas Periódicas

El sistema NAC utiliza **APScheduler** para ejecutar tareas periódicas en background.

## Tareas Configuradas

### 1. Health Check (cada 60 segundos)
**Función**: `tasks.health_check()`

Verifica la disponibilidad y latencia del router RouterOS.

- Envía un ping al router
- Registra latencia en ms
- Marca como "ok" o "error"
- Registra en tabla `router_sync_log`

### 2. Sincronización ARP (cada 5 minutos)
**Función**: `tasks.sync_arp()`

Sincroniza la tabla ARP del router con la BD local.

- Obtiene tabla ARP actual del router
- Actualiza `last_seen` de dispositivos activos
- Registra dispositivos vivos
- Mantiene estado sincronizado

### 3. Snapshots de Tráfico (cada 5 minutos)
**Función**: `tasks.collect_traffic_snapshots()`

Recolecta métricas de tráfico de cada dispositivo.

- Obtiene interfaz de cada dispositivo
- Registra bytes_in/out, packets
- Inserta en tabla `traffic_snapshots`
- Usado para gráficos y análisis

### 4. Verificar Dispositivos Expirados (cada 10 minutos)
**Función**: `tasks.check_expired_devices()`

Detecta dispositivos cuyo acceso ha expirado.

- Consulta columna `expires_at`
- Marca dispositivo como "expired"
- Bloquea en router (blacklist)
- Cierra sesiones activas

### 5. Actualizar Dispositivos Vivos (cada 2 minutos)
**Función**: `tasks.update_live_devices()`

Mantiene actualizado el estado de dispositivos online/offline.

- Compara con tabla ARP actual
- Marca offline si no aparece en ARP
- Cierra sesión si estaba activa
- Usa para dashboard en tiempo real

### 6. Sincronizar QoS Queues (cada 15 minutos)
**Función**: `tasks.sync_queues()`

Sincroniza perfiles QoS con el router.

- Obtiene dispositivos con perfil asignado
- Crea o actualiza queues en router
- Aplica límites de ancho de banda
- Registra en `router_sync_log`

### 7. Limpieza de Datos Antiguos (cada 24 horas)
**Función**: `tasks.cleanup_old_data()`

Mantiene la BD optimizada eliminando datos antiguos.

- Elimina snapshots > 30 días
- Elimina sync logs > 7 días
- Libera espacio en disco
- Mejora performance

### 8. Sincronizar Entradas DNS (cada 24 horas)
**Función**: `tasks.sync_dns_entries()`

Sincroniza dominios bloqueados con el router.

- Obtiene entradas de tabla `dns_entries`
- Las agrega al servidor DNS del router
- Mantiene sincronización manual

## Configuración

Las tareas se configuran en `app/config.py`:

```python
HEALTH_CHECK_INTERVAL = 60          # Health check cada 60 segundos
TRAFFIC_SYNC_INTERVAL = 300         # ARP y tráfico cada 5 minutos
EXPIRY_CHECK_INTERVAL = 600         # Expiración cada 10 minutos
```

## Logging

Todas las tareas registran en `logging`:

```
[INFO] Health check del router
[INFO] ARP sync completado: 45 dispositivos
[INFO] Traffic snapshots recolectados
[WARNING] Router health check failed: Connection timeout
[ERROR] Error en QoS sync: ...
```

## Manejo de Errores

Cada tarea tiene try/except y registra:

- **router_sync_log**: Para operaciones del router
- **audit_log**: Para cambios en BD (si aplica)
- **logs**: Para debugging

Si una tarea falla:
- No detiene el scheduler
- Se reintentar en la próxima ejecución
- Se registra el error en logs

## Monitoreo

Para ver tareas activas:

```python
from app.scheduler import get_scheduler

scheduler = await get_scheduler()
jobs = scheduler.get_jobs()

# Retorna:
# [
#   {"id": "health_check", "name": "Health Check", "next_run_time": "..."},
#   {"id": "sync_arp", "name": "ARP Sync", "next_run_time": "..."},
#   ...
# ]
```

## Integración con FastAPI

El scheduler se inicializa automáticamente con la aplicación:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = await init_db()
    scheduler = await init_scheduler(db, router)
    
    yield
    
    # Shutdown
    await stop_scheduler()
```

## Troubleshooting

### Scheduler no inicia
- Verificar que APScheduler esté instalado: `pip install apscheduler`
- Ver logs de startup en la consola
- Verificar configuración en `app/config.py`

### Tareas no se ejecutan
- Verificar que la aplicación FastAPI está corriendo
- Ver logs de DEBUG para ver ejecuciones
- Revisar conexión con router

### Errores de conexión con router
- Verificar IP y puerto del router en `.env`
- Verificar credenciales RouterOS
- Ver health check en logs

## Extensión con Nuevas Tareas

Para agregar una nueva tarea:

1. Crear método en `app/scheduler/tasks.py`:

```python
async def mi_tarea(self):
    try:
        # Lógica
        logger.info("Tarea completada")
    except Exception as e:
        logger.error(f"Error en mi_tarea: {e}")
```

2. Registrar en `app/scheduler/manager.py`:

```python
self.scheduler.add_job(
    self.tasks.mi_tarea,
    trigger=IntervalTrigger(seconds=300),
    name="mi_tarea",
    id="mi_tarea",
    replace_existing=True,
)
```

3. (Opcional) Agregar configuración en `app/config.py`:

```python
MI_TAREA_INTERVAL = int(os.getenv("MI_TAREA_INTERVAL", "300"))
```
