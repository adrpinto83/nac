# 📡 Cliente RouterOS — API Reference

**Entregable 3**  
**Fecha:** 2025-06-11

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Uso básico](#uso-básico)
4. [Métodos de lectura de estado](#métodos-de-lectura-de-estado)
5. [Métodos de access control](#métodos-de-access-control)
6. [Métodos de QoS](#métodos-de-qos)
7. [Métodos de DNS](#métodos-de-dns)
8. [Health checks](#health-checks)
9. [Excepciones](#excepciones)
10. [Ejemplos completos](#ejemplos-completos)

---

## Introducción

El **RouterOSClient** es un cliente REST async para MikroTik RouterOS, implementado con `httpx` para máximo rendimiento en operaciones asincrónicas.

**Características:**
- ✅ Async/await con AsyncIO
- ✅ Autenticación HTTP Basic
- ✅ Retry automático con backoff exponencial
- ✅ Manejo robusto de errores
- ✅ Type hints completos
- ✅ Data classes tipadas para respuestas
- ✅ Context manager (with async)
- ✅ Health checks integrados

---

## Instalación

```bash
pip install httpx>=0.24.0
```

---

## Uso básico

### Conexión simple

```python
from routeros.client import RouterOSClient

client = RouterOSClient(
    host="192.168.88.1",
    port=80,
    username="api-container",
    password="NAC_MikroTik_2025"
)

# Conectar
await client.connect()

# Usar
identity = await client.get_router_identity()
print(identity.name)

# Desconectar
await client.disconnect()
```

### Context manager (recomendado)

```python
async with RouterOSClient() as client:
    identity = await client.get_router_identity()
    arp_table = await client.get_arp_table()
    # Se desconecta automáticamente
```

### Parámetros de inicialización

```python
client = RouterOSClient(
    host="192.168.88.1",        # IP del router (default)
    port=80,                     # Puerto REST API (default)
    username="api-container",    # Usuario API (default)
    password="NAC_...",          # Contraseña (default)
    timeout=10.0,                # Timeout en segundos (default)
    verify_ssl=False,            # Verificar SSL (default: False)
    max_retries=3                # Reintentos máximos (default)
)
```

---

## Métodos de lectura de estado

Estos métodos leen el estado actual del router sin modificar nada.

### `get_router_identity() → RouterIdentity`

Obtiene información de identidad del router.

```python
identity = await client.get_router_identity()
print(identity.name)      # "hAP ac3"
print(identity.platform)  # "RouterOS 7.x"
```

**Retorna:**
```python
@dataclass
class RouterIdentity:
    name: str
    platform: Optional[str]
```

---

### `get_arp_table() → List[ARPEntry]`

Obtiene tabla ARP (dispositivos activos en la red).

```python
arp_entries = await client.get_arp_table()
for entry in arp_entries:
    print(f"{entry.mac_address} → {entry.address} en {entry.interface}")
```

**Retorna:**
```python
@dataclass
class ARPEntry:
    mac_address: str      # AA:BB:CC:DD:EE:FF
    address: str          # 192.168.88.100
    interface: str        # "bridge-lan"
    disabled: bool        # False
    dynamic: bool         # True
```

---

### `get_dhcp_leases() → List[DHCPLease]`

Obtiene leases DHCP activos (IPs asignadas).

```python
leases = await client.get_dhcp_leases()
for lease in leases:
    print(f"MAC {lease.mac_address} → IP {lease.address}")
```

**Retorna:**
```python
@dataclass
class DHCPLease:
    mac_address: str      # AA:BB:CC:DD:EE:FF
    address: str          # 192.168.88.100
    server: str           # "dhcp-server"
    disabled: bool        # False
    comment: Optional[str]
```

---

### `get_hotspot_active() → List[HotspotActive]`

Obtiene sesiones activas de hotspot.

```python
sessions = await client.get_hotspot_active()
for session in sessions:
    print(f"Usuario {session.user} desde {session.address}")
```

---

### `get_interfaces() → List[Interface]`

Obtiene estadísticas de interfaces.

```python
interfaces = await client.get_interfaces()
for iface in interfaces:
    print(f"{iface.name}: {iface.rx_byte} bytes entrada")
```

---

### `get_simple_queues() → List[SimpleQueue]`

Obtiene todas las simple queues (QoS).

```python
queues = await client.get_simple_queues()
for queue in queues:
    print(f"{queue.name}: {queue.bytes_in}/{queue.bytes_out}")
```

---

### `get_address_lists() → List[AddressListEntry]`

Obtiene todas las entradas de address-list (whitelist, blocklist).

```python
entries = await client.get_address_lists()
whitelist = [e for e in entries if e.list == "mac-whitelist"]
blocklist = [e for e in entries if e.list == "mac-blocked"]
```

---

### `get_dns_static() → List[DNSStaticEntry]`

Obtiene entradas DNS estáticas bloqueadas.

```python
dns_entries = await client.get_dns_static()
for entry in dns_entries:
    print(f"{entry.name} → {entry.address}")
```

---

## Métodos de access control

Estos métodos modifican las listas de whitelist/blocklist.

### `add_to_address_list(list_name, address, comment, timeout) → str`

Agrega MAC o IP a una lista.

```python
# Agregar a whitelist
entry_id = await client.add_to_address_list(
    list_name="mac-whitelist",
    address="AA:BB:CC:DD:EE:FF",
    comment="Laptop de John"
)

# Agregar con timeout
entry_id = await client.add_to_address_list(
    list_name="mac-blocked",
    address="XX:XX:XX:XX:XX:XX",
    comment="Bloqueado temporalmente",
    timeout="00:10:00"  # 10 minutos
)
```

**Parámetros:**
- `list_name`: "mac-whitelist" o "mac-blocked"
- `address`: MAC o IP
- `comment`: Descripción (opcional)
- `timeout`: Duración (formato "HH:MM:SS", opcional)

**Retorna:**
- ID de la entrada creada (string)

---

### `remove_from_address_list(entry_id) → bool`

Elimina una entrada de la lista.

```python
success = await client.remove_from_address_list("*123")
```

---

### `update_address_list_entry(entry_id, disabled, comment) → bool`

Actualiza una entrada (deshabilitar/comentario).

```python
# Deshabilitar sin eliminar
await client.update_address_list_entry(
    entry_id="*123",
    disabled=True
)

# Cambiar comentario
await client.update_address_list_entry(
    entry_id="*123",
    comment="Nuevo comentario"
)
```

---

## Métodos de QoS

Estos métodos manejan simple queues (control de ancho de banda).

### `create_queue(name, target, max_limit, priority, comment) → str`

Crea nueva queue de QoS.

```python
queue_id = await client.create_queue(
    name="User-192.168.88.100",
    target="192.168.88.100/32",
    max_limit="5M/2M",  # 5 Mbps up / 2 Mbps down
    priority=3,
    comment="Usuario de prueba"
)
```

**Parámetros:**
- `name`: Nombre único de la cola
- `target`: IP o rango CIDR del dispositivo
- `max_limit`: Formato "UPLOAD/DOWNLOAD" (ej: "10M/5M")
- `priority`: 1 (máxima) a 8 (mínima)
- `comment`: Descripción (opcional)

**Retorna:**
- ID de queue creada

---

### `update_queue(queue_id, max_limit, priority, disabled) → bool`

Actualiza límites de una queue.

```python
# Cambiar límite de velocidad
await client.update_queue(
    queue_id="*456",
    max_limit="10M/5M"
)

# Deshabilitar temporalmente
await client.update_queue(
    queue_id="*456",
    disabled=True
)
```

---

### `delete_queue(queue_id) → bool`

Elimina una queue.

```python
success = await client.delete_queue("*456")
```

---

## Métodos de DNS

Estos métodos manejan entradas DNS estáticas (bloqueo de dominios).

### `add_dns_entry(domain, address, comment) → str`

Agrega bloqueo DNS para un dominio.

```python
# Bloquear Facebook
entry_id = await client.add_dns_entry(
    domain="facebook.com",
    address="0.0.0.0",  # Redirige a 0.0.0.0 (bloquea)
    comment="Redes sociales bloqueadas"
)

# Bloquear también www.facebook.com
await client.add_dns_entry("www.facebook.com", "0.0.0.0")
```

**Parámetros:**
- `domain`: Dominio a bloquear
- `address`: IP de redirección (default: "0.0.0.0" = bloquea)
- `comment`: Descripción (opcional)

**Retorna:**
- ID de entrada creada

---

### `delete_dns_entry(entry_id) → bool`

Elimina un bloqueo DNS.

```python
success = await client.delete_dns_entry("*789")
```

---

## Health checks

Estos métodos verifican el estado del router.

### `health_check() → HealthCheckResult`

Realiza health check completo.

```python
result = await client.health_check()
if result.status == "ok":
    print(f"Router OK (latencia: {result.latency_ms}ms)")
else:
    print(f"Error: {result.message}")
```

**Retorna:**
```python
@dataclass
class HealthCheckResult:
    status: str              # "ok" o "error"
    latency_ms: float        # Latencia en milisegundos
    timestamp: str           # ISO timestamp
    message: Optional[str]   # Información adicional
```

---

### `test_connection() → bool`

Test simple de conectividad (retorna True/False).

```python
is_connected = await client.test_connection()
if is_connected:
    print("Router accesible")
else:
    print("Router no accesible")
```

---

### `is_connected() → bool`

Verifica estado de conexión.

```python
if client.is_connected():
    # Usar cliente
    pass
```

---

## Excepciones

El cliente lanza excepciones tipadas para cada tipo de error.

### Jerarquía de excepciones

```
RouterOSException (base)
├── RouterOSConnectionError      # No se puede conectar
├── RouterOSAuthError            # Credenciales inválidas (401)
├── RouterOSNotFoundError        # Endpoint no existe (404)
├── RouterOSValidationError      # Datos inválidos (422)
├── RouterOSServerError          # Error servidor (500)
├── RouterOSTimeoutError         # Timeout de conexión
└── RouterOSInvalidResponseError # Respuesta malformada
```

### Manejo de excepciones

```python
from routeros.exceptions import (
    RouterOSAuthError,
    RouterOSConnectionError,
    RouterOSTimeoutError,
)

try:
    async with RouterOSClient() as client:
        arp = await client.get_arp_table()
except RouterOSAuthError:
    print("Credenciales incorrectas")
except RouterOSConnectionError as e:
    print(f"No se puede conectar: {e.reason}")
except RouterOSTimeoutError as e:
    print(f"Timeout después de {e.timeout_seconds}s")
except Exception as e:
    print(f"Error inesperado: {e}")
```

---

## Ejemplos completos

### Ejemplo 1: Leer estado de red

```python
import asyncio
from routeros.client import RouterOSClient

async def check_network():
    async with RouterOSClient() as client:
        # Identidad
        identity = await client.get_router_identity()
        print(f"Router: {identity.name}")

        # Dispositivos en red
        arp = await client.get_arp_table()
        print(f"\nDispositivos conectados: {len(arp)}")
        for entry in arp:
            print(f"  {entry.mac_address} → {entry.address}")

        # Leases DHCP
        leases = await client.get_dhcp_leases()
        print(f"\nIPs asignadas: {len(leases)}")

        # Health check
        health = await client.health_check()
        print(f"\nLatencia: {health.latency_ms:.1f}ms")

asyncio.run(check_network())
```

### Ejemplo 2: Registrar dispositivo

```python
async def register_device(mac: str, name: str, profile: str):
    """Registra un dispositivo en el router."""
    async with RouterOSClient() as client:
        # Agregar a whitelist
        await client.add_to_address_list(
            list_name="mac-whitelist",
            address=mac,
            comment=f"{name} ({profile})"
        )
        print(f"✓ {mac} agregada a whitelist")

        # Crear queue QoS
        max_limits = {
            "admin": "0/0",
            "profesional": "10M/5M",
            "estandar": "5M/2M",
            "invitado": "2M/1M",
        }
        
        queue_id = await client.create_queue(
            name=f"{name}-queue",
            target=f"192.168.88.100/32",  # IP real
            max_limit=max_limits.get(profile, "5M/2M"),
            comment=name
        )
        print(f"✓ Queue {queue_id} creada")

asyncio.run(register_device("AA:BB:CC:DD:EE:FF", "John Laptop", "profesional"))
```

### Ejemplo 3: Bloquear y desbloquear

```python
async def block_user(mac: str, reason: str = ""):
    """Bloquea un dispositivo."""
    async with RouterOSClient() as client:
        # Obtener entrada actual
        entries = await client.get_address_lists()
        entry = next((e for e in entries if e.address == mac), None)
        
        if entry:
            # Deshabilitar en whitelist
            await client.update_address_list_entry(
                entry_id=entry.id,
                disabled=True,
                comment=f"Bloqueado: {reason}"
            )
            print(f"✓ {mac} bloqueada")

async def unblock_user(mac: str):
    """Desbloquea un dispositivo."""
    async with RouterOSClient() as client:
        entries = await client.get_address_lists()
        entry = next((e for e in entries if e.address == mac), None)
        
        if entry:
            await client.update_address_list_entry(
                entry_id=entry.id,
                disabled=False,
                comment="Activo"
            )
            print(f"✓ {mac} desbloqueada")

asyncio.run(block_user("AA:BB:CC:DD:EE:FF", "Violación de política"))
asyncio.run(unblock_user("AA:BB:CC:DD:EE:FF"))
```

### Ejemplo 4: Gestionar DNS

```python
async def block_websites(websites: list, category: str):
    """Bloquea lista de sitios web."""
    async with RouterOSClient() as client:
        for website in websites:
            entry_id = await client.add_dns_entry(
                domain=website,
                address="0.0.0.0",
                comment=f"Categoría: {category}"
            )
            print(f"✓ {website} bloqueado")

async def unblock_websites(websites: list):
    """Desbloquea lista de sitios."""
    async with RouterOSClient() as client:
        all_dns = await client.get_dns_static()
        
        for website in websites:
            entry = next((e for e in all_dns if e.name == website), None)
            if entry:
                await client.delete_dns_entry(entry.id)
                print(f"✓ {website} desbloqueado")

asyncio.run(block_websites(["facebook.com", "www.facebook.com"], "Redes sociales"))
```

---

## Integración con FastAPI

```python
# En app/dependencies.py
from routeros.client import RouterOSClient

async def get_router_client() -> RouterOSClient:
    """Dependency: obtiene cliente RouterOS."""
    async with RouterOSClient() as client:
        yield client

# En un router
from fastapi import Depends
from routeros.client import RouterOSClient

@app.get("/api/devices/live")
async def get_live_devices(router: RouterOSClient = Depends(get_router_client)):
    """Obtiene MACs visibles en la red ahora."""
    arp = await router.get_arp_table()
    return [{"mac": e.mac_address, "ip": e.address} for e in arp]
```

---

**Documentación completada ✅**
