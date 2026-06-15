# 🔗 INTEGRACIÓN API REST - MikroTik NAC System

**Documentación completa para integración bidireccional con la aplicación NAC**

---

## 📋 Índice

1. [Endpoints Disponibles](#endpoints-disponibles)
2. [Autenticación](#autenticación)
3. [Estructura de Requests](#estructura-de-requests)
4. [Estructura de Responses](#estructura-de-responses)
5. [Ejemplos de Integración](#ejemplos-de-integración)
6. [Templates Predefinidos](#templates-predefinidos)
7. [Sincronización de Datos](#sincronización-de-datos)
8. [Futuros Cambios](#futuros-cambios)

---

## 🔗 Endpoints Disponibles

### Sistema y Estado

#### GET `/rest/system/identity`
**Descripción:** Obtener información del router
```json
{
  "name": "MikroTik",
  "version": "7.x",
  "build": "xxxxx"
}
```

#### GET `/rest/system/resource`
**Descripción:** Recursos del sistema
```json
{
  "uptime": "1h23m",
  "cpu-count": 1,
  "memory-total": 268435456,
  "memory-used": 123456789,
  "free-memory": 145000000
}
```

#### GET `/rest/system/health`
**Descripción:** Estado de salud del router
```json
{
  "temperature": 45,
  "voltage": 12.5
}
```

---

### Interfaces y Conectividad

#### GET `/rest/interface`
**Descripción:** Lista todas las interfaces
**Response:** Array de objetos
```json
[
  {
    ".id": "*1",
    "name": "ether1-isp1",
    "type": "ether",
    "mtu": 1500,
    "mac-address": "AA:BB:CC:DD:EE:FF",
    "running": true
  },
  ...
]
```

**Endpoints relacionados:**
- `GET /rest/interface/ethernet` - Solo interfaces ethernet
- `GET /rest/interface/bridge` - Puentes
- `GET /rest/interface/vlan` - VLANs

---

### Configuración IP

#### GET `/rest/ip/address`
**Descripción:** Direcciones IP configuradas
```json
[
  {
    ".id": "*1",
    "address": "192.168.88.5/24",
    "interface": "ether5-admin",
    "network": "192.168.88.0",
    "disabled": false
  },
  ...
]
```

#### GET `/rest/ip/route`
**Descripción:** Tabla de rutas (MUY IMPORTANTE para failover)
```json
[
  {
    ".id": "*1",
    "dst-address": "0.0.0.0/0",
    "gateway": "203.0.113.1",
    "distance": 1,
    "target-scope": "10",
    "active": true
  },
  {
    ".id": "*2",
    "dst-address": "0.0.0.0/0",
    "gateway": "198.51.100.1",
    "distance": 2,
    "target-scope": "10",
    "active": false
  }
]
```

---

### DHCP (Crucial para NAC)

#### GET `/rest/ip/dhcp-client`
**Descripción:** Clientes DHCP (ISPs)
```json
[
  {
    ".id": "*1",
    "interface": "ether1-isp1",
    "disabled": false,
    "status": "bound",
    "address": "203.0.113.50/24",
    "server": "203.0.113.1",
    "gateway": "203.0.113.1"
  },
  {
    ".id": "*2",
    "interface": "ether2-isp2",
    "disabled": false,
    "status": "bound",
    "address": "198.51.100.50/24",
    "server": "198.51.100.1",
    "gateway": "198.51.100.1"
  }
]
```

#### GET `/rest/ip/dhcp-server`
**Descripción:** Servidores DHCP
```json
[
  {
    ".id": "*1",
    "name": "dhcp-aps",
    "interface": "ether5-admin",
    "disabled": false
  }
]
```

#### GET `/rest/ip/dhcp-server/network`
**Descripción:** Redes DHCP configuradas
```json
[
  {
    ".id": "*1",
    "address": "192.168.88.0/24",
    "gateway": "192.168.88.1",
    "dns-server": "8.8.8.8,8.8.4.4"
  }
]
```

#### 🔴 **CRITICAL:** `GET /rest/ip/dhcp-server/lease`
**Descripción:** Dispositivos conectados (TABLA ARP) - ENDPOINT MÁS IMPORTANTE
```json
[
  {
    ".id": "*1",
    "address": "192.168.88.10",
    "mac-address": "AA:BB:CC:DD:EE:01",
    "client-id": "usuario-1",
    "host-name": "laptop-admin",
    "server": "dhcp-aps",
    "status": "bound",
    "expires-after": "8h45m23s",
    "last-seen": "3s"
  },
  {
    ".id": "*2",
    "address": "192.168.88.11",
    "mac-address": "AA:BB:CC:DD:EE:02",
    "host-name": "ap-wifi-1",
    "status": "bound",
    "expires-after": "10h",
    "last-seen": "1s"
  }
]
```

---

### NAT y Firewall (Control de Acceso)

#### GET `/rest/ip/firewall/nat`
**Descripción:** Reglas NAT (Masquerade)
```json
[
  {
    ".id": "*1",
    "chain": "srcnat",
    "out-interface": "ether1-isp1",
    "action": "masquerade",
    "disabled": false
  },
  {
    ".id": "*2",
    "chain": "srcnat",
    "out-interface": "ether2-isp2",
    "action": "masquerade",
    "disabled": false
  }
]
```

#### GET `/rest/ip/firewall/filter`
**Descripción:** Reglas Forward (Firewall)
```json
[
  {
    ".id": "*1",
    "chain": "forward",
    "action": "accept",
    "connection-state": "established,related",
    "disabled": false
  },
  {
    ".id": "*2",
    "chain": "forward",
    "action": "drop",
    "connection-state": "invalid",
    "disabled": false
  }
]
```

#### GET `/rest/ip/firewall/address-list`
**Descripción:** Listas de direcciones (para whitelist/blacklist)
```json
[
  {
    ".id": "*1",
    "list": "whitelist",
    "address": "AA:BB:CC:DD:EE:FF",
    "comment": "MAC permitida"
  }
]
```

---

### QoS (Ancho de Banda)

#### GET `/rest/queue/simple`
**Descripción:** Colas simples (Control de ancho de banda)
```json
[
  {
    ".id": "*1",
    "name": "user-1-limit",
    "target": "192.168.88.10",
    "max-limit": "5M/2M",
    "priority": 8
  }
]
```

---

### DNS

#### GET `/rest/ip/dns`
**Descripción:** Configuración DNS
```json
{
  "servers": "8.8.8.8,8.8.4.4",
  "allow-remote-requests": true,
  "cache-max-ttl": "1w"
}
```

#### GET `/rest/ip/dns/static`
**Descripción:** Registros DNS estáticos
```json
[
  {
    ".id": "*1",
    "name": "google.com",
    "address": "142.251.41.14"
  }
]
```

---

## 🔐 Autenticación

### Método 1: Basic Auth (Recomendado para NAC System)
```python
import httpx

client = httpx.Client(
    base_url="http://192.168.88.1:8728",
    auth=("admin", ""),  # Usuario, password (vacío en factory reset)
    verify=False
)
```

### Método 2: Sin autenticación (Factory Reset)
```python
client = httpx.Client(
    base_url="http://192.168.88.1:8728",
    verify=False
)
```

### Puertos disponibles
- **8728**: HTTP REST API
- **8729**: HTTPS REST API
- **80**: WebFig (Interfaz web)

---

## 📤 Estructura de Requests

### GET Request (Lectura)
```python
# Obtener DHCP leases (dispositivos conectados)
response = client.get("/rest/ip/dhcp-server/lease")
devices = response.json()
```

### POST Request (Crear/Agregar)
```python
# Crear address-list (whitelist)
data = {
    "list": "whitelist",
    "address": "AA:BB:CC:DD:EE:FF",
    "comment": "MAC permitida"
}
response = client.post("/rest/ip/firewall/address-list", json=data)
address_id = response.json()[".id"]
```

### PUT Request (Modificar)
```python
# Modificar queue (límite de ancho de banda)
data = {
    "max-limit": "10M/5M"
}
response = client.put("/rest/queue/simple/*1", json=data)
```

### DELETE Request (Eliminar)
```python
# Eliminar una regla
response = client.delete("/rest/ip/firewall/filter/*1")
```

---

## 📥 Estructura de Responses

### Lista (Array)
```json
[
  {
    ".id": "*1",
    "property1": "value1",
    "property2": "value2"
  },
  {
    ".id": "*2",
    "property1": "value3",
    "property2": "value4"
  }
]
```

### Objeto (Dict)
```json
{
  "property1": "value1",
  "property2": "value2"
}
```

### Objeto creado (POST)
```json
{
  ".id": "*3"
}
```

---

## 💡 Ejemplos de Integración

### Ejemplo 1: Obtener dispositivos conectados (para NAC Dashboard)
```python
async def get_connected_devices():
    """Obtener todos los dispositivos conectados al router"""
    
    async with httpx.AsyncClient(
        base_url="http://192.168.88.1:8728",
        verify=False
    ) as client:
        response = await client.get("/rest/ip/dhcp-server/lease")
        leases = response.json()
        
        devices = []
        for lease in leases:
            devices.append({
                "mac_address": lease["mac-address"],
                "ip_address": lease["address"],
                "hostname": lease.get("host-name", "Unknown"),
                "status": lease["status"],
                "expires_after": lease.get("expires-after", "N/A"),
                "last_seen": lease.get("last-seen", "N/A")
            })
        
        return devices
```

### Ejemplo 2: Verificar estado de ISPs (Load Balancing + Failover)
```python
async def check_isp_status():
    """Verificar qué ISPs están activos"""
    
    async with httpx.AsyncClient(
        base_url="http://192.168.88.1:8728",
        verify=False
    ) as client:
        # Obtener DHCP clients
        response = await client.get("/rest/ip/dhcp-client")
        clients = response.json()
        
        isp_status = {}
        for client in clients:
            interface = client["interface"]
            status = client.get("status", "down")
            address = client.get("address", "No IP")
            
            isp_status[interface] = {
                "status": "ONLINE" if status == "bound" else "OFFLINE",
                "ip": address,
                "gateway": client.get("server", "N/A")
            }
        
        return isp_status
```

### Ejemplo 3: Agregar/Bloquear un dispositivo (Whitelist/Blacklist)
```python
async def add_to_whitelist(mac_address: str, comment: str = ""):
    """Agregar MAC a whitelist"""
    
    async with httpx.AsyncClient(
        base_url="http://192.168.88.1:8728",
        verify=False
    ) as client:
        data = {
            "list": "whitelist",
            "address": mac_address,
            "comment": comment
        }
        response = await client.post("/rest/ip/firewall/address-list", json=data)
        return response.json()

async def remove_from_whitelist(mac_address: str):
    """Remover MAC de whitelist"""
    
    async with httpx.AsyncClient(
        base_url="http://192.168.88.1:8728",
        verify=False
    ) as client:
        # Primero obtener el ID
        lists = await client.get("/rest/ip/firewall/address-list")
        for item in lists.json():
            if item["address"] == mac_address:
                # Eliminar
                await client.delete(f"/rest/ip/firewall/address-list/{item['.id']}")
                return True
        return False
```

### Ejemplo 4: Establecer límite de ancho de banda
```python
async def set_bandwidth_limit(ip_address: str, down: str, up: str):
    """Establecer límite de ancho de banda para IP"""
    
    async with httpx.AsyncClient(
        base_url="http://192.168.88.1:8728",
        verify=False
    ) as client:
        # Crear queue simple
        data = {
            "target": ip_address,
            "max-limit": f"{down}/{up}",
            "priority": 8
        }
        response = await client.post("/rest/queue/simple", json=data)
        return response.json()
```

---

## 📋 Templates Predefinidos

### Template 1: Cliente API del Router
```python
# app/services/router_client.py

import httpx
from typing import List, Dict, Optional

class MikroTikRouter:
    def __init__(self, host: str = "192.168.88.1", port: int = 8728):
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            verify=False,
            timeout=10
        )
    
    async def get_devices(self) -> List[Dict]:
        """Obtener dispositivos conectados"""
        response = await self.client.get("/rest/ip/dhcp-server/lease")
        return response.json()
    
    async def get_isp_status(self) -> Dict:
        """Obtener estado de ISPs"""
        response = await self.client.get("/rest/ip/dhcp-client")
        clients = response.json()
        
        status = {}
        for c in clients:
            status[c["interface"]] = c.get("status", "down")
        return status
    
    async def add_whitelist(self, mac: str) -> bool:
        """Agregar a whitelist"""
        data = {"list": "whitelist", "address": mac}
        response = await self.client.post("/rest/ip/firewall/address-list", json=data)
        return response.status_code == 200
    
    async def get_routes(self) -> List[Dict]:
        """Obtener tabla de rutas (para monitoreo)"""
        response = await self.client.get("/rest/ip/route")
        return response.json()
    
    async def close(self):
        """Cerrar conexión"""
        await self.client.aclose()
```

### Template 2: Sincronización automática
```python
# app/scheduler/tasks.py

from app.services.router_client import MikroTikRouter

async def sync_devices_from_router():
    """Sincronizar dispositivos conectados cada 60 segundos"""
    router = MikroTikRouter()
    
    devices = await router.get_devices()
    
    for device in devices:
        # Guardar en BD
        await Device.create(
            mac_address=device["mac-address"],
            ip_address=device["address"],
            hostname=device.get("host-name"),
            status=device["status"]
        )
    
    await router.close()

async def check_isp_failover():
    """Verificar failover cada 30 segundos"""
    router = MikroTikRouter()
    
    status = await router.get_isp_status()
    routes = await router.get_routes()
    
    # Lógica de failover
    isp1_active = status.get("ether1-isp1") == "bound"
    isp2_active = status.get("ether2-isp2") == "bound"
    
    if not isp1_active and not isp2_active:
        # ALERT: Sin Internet
        await Alert.create(
            level="critical",
            message="Ambos ISPs están DOWN",
            affected_users=await count_active_users()
        )
    
    await router.close()
```

---

## 🔄 Sincronización de Datos

### Sincronización: Router → Aplicación

```
┌─────────────────┐
│   MikroTik      │
│   DHCP Leases   │ ──→ GET /rest/ip/dhcp-server/lease
└─────────────────┘
        ↓
   [Procesar]
        ↓
┌─────────────────┐
│   NAC Database  │
│   - Users       │
│   - Devices     │
│   - Sessions    │
└─────────────────┘
```

**Frecuencia recomendada:**
- Dispositivos conectados: **30 segundos** (crítico para NAC)
- Estado de ISPs: **30 segundos** (crítico para failover)
- Rutas activas: **60 segundos** (monitoreo)
- Stats de QoS: **300 segundos** (análisis)

### Sincronización: Aplicación → Router

```
┌─────────────────┐
│  NAC System     │
│  - Whitelist    │
│  - QoS Rules    │
│  - Firewall     │
└─────────────────┘
        ↓
   [Acciones]
        ↓
┌─────────────────┐
│   MikroTik      │
│   Firewall      │ ←─ POST/PUT address-list
│   QoS           │ ←─ POST/PUT queue/simple
│   ACL           │ ←─ POST/PUT firewall/filter
└─────────────────┘
```

---

## 🔮 Futuros Cambios

### Cómo agregar nuevos endpoints

#### Paso 1: Identificar endpoint en MikroTik
```
Ir a: http://192.168.88.1/webfig
Menu → (selector) → Ver ruta REST correspondiente
```

#### Paso 2: Documentar endpoint
```markdown
#### GET `/rest/path/to/resource`
**Descripción:** Qué hace
**Response:** Estructura JSON esperada
```

#### Paso 3: Agregar método en RouterClient
```python
async def get_my_resource(self) -> List[Dict]:
    """Obtener recurso personalizado"""
    response = await self.client.get("/rest/path/to/resource")
    return response.json()
```

#### Paso 4: Crear endpoint en API NAC
```python
@router.get("/api/my-resource")
async def get_my_resource(current_user = Depends(require_admin)):
    """Obtener recurso personalizado"""
    router = MikroTikRouter()
    data = await router.get_my_resource()
    await router.close()
    return data
```

#### Paso 5: Documentar en esta guía
```
Agregar sección en: Endpoints Disponibles
Incluir ejemplo de uso en: Ejemplos de Integración
```

---

## ✅ Checklist de Verificación

- [x] Endpoint `/rest/system/identity` → Información router
- [x] Endpoint `/rest/interface` → Interfaces disponibles
- [x] Endpoint `/rest/ip/address` → IPs configuradas
- [x] Endpoint `/rest/ip/dhcp-client` → Estado ISPs ⭐
- [x] Endpoint `/rest/ip/dhcp-server/lease` → Dispositivos conectados ⭐⭐⭐
- [x] Endpoint `/rest/ip/firewall/nat` → NAT rules
- [x] Endpoint `/rest/ip/firewall/address-list` → Whitelist/Blacklist
- [x] Endpoint `/rest/queue/simple` → QoS
- [x] Endpoint `/rest/ip/route` → Rutas (Failover) ⭐

---

## 📞 Endpoints Críticos para NAC

| Prioridad | Endpoint | Uso |
|-----------|----------|-----|
| 🔴 **CRÍTICA** | `/rest/ip/dhcp-server/lease` | Ver dispositivos conectados |
| 🔴 **CRÍTICA** | `/rest/ip/dhcp-client` | Monitorear ISPs (failover) |
| 🟠 **ALTA** | `/rest/ip/firewall/address-list` | Whitelist/Blacklist |
| 🟠 **ALTA** | `/rest/queue/simple` | Control de QoS |
| 🟡 **MEDIA** | `/rest/ip/route` | Rutas activas |
| 🟡 **MEDIA** | `/rest/interface` | Estado de interfaces |

---

**✅ API REST lista para integración con la aplicación NAC.**

Todos los endpoints están documentados y predefinidos para futuros cambios.
