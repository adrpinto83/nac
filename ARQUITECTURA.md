# 🏗️ ARQUITECTURA — Sistema NAC

**Entregable 2 (Parte 2)**  
**Fecha:** 2025-06-11

---

## 🎯 Principios de diseño

1. **Separación de responsabilidades:** Cada módulo tiene un rol único
2. **Async-first:** Todo async con AsyncIO (no bloquea operaciones)
3. **Stateless API:** Cada request es independiente (sin sesiones en servidor)
4. **JWT para autenticación:** Token en cliente (localStorage)
5. **REST puro:** Endpoints CRUD siguiendo convenciones HTTP
6. **BD local:** SQLite en la PC, no en el router
7. **Failsafe:** Reglas en router persisten aunque la app se caiga

---

## 📊 Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NAVEGADOR WEB (Usuario)                         │
├─────────────────────────────────────────────────────────────────────┤
│  Login.html → Dashboard.html → Users.html → Devices.html → etc.    │
│  (fetch → /api/... → recibe JSON → actualiza DOM)                  │
├─────────────────────────────────────────────────────────────────────┤
│                    APLICACIÓN FASTAPI (PC Local)                    │
│                         http://localhost:8080                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Routers (Endpoints)                                        │  │
│  │  ├─ POST /api/auth/login                                    │  │
│  │  ├─ GET  /api/users (con paginación)                        │  │
│  │  ├─ POST /api/users (crear usuario)                         │  │
│  │  ├─ PUT  /api/users/{id} (actualizar usuario)               │  │
│  │  ├─ GET  /api/devices/live (MACs visibles en red)           │  │
│  │  ├─ GET  /api/dashboard (métricas tiempo real)              │  │
│  │  ├─ POST /api/dns/entries (bloquear dominio)                │  │
│  │  ├─ GET  /api/history/{user_id} (historial)                 │  │
│  │  └─ GET  /api/audit (log de auditoría)                      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Middleware                                                 │  │
│  │  ├─ CORS (acepta requests desde navegador)                  │  │
│  │  ├─ JWT (verifica token en Authorization header)            │  │
│  │  ├─ Roles (SUPERADMIN, ADMIN_RED, SOPORTE)                 │  │
│  │  └─ Error Handler (try/catch global)                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Services (Lógica de negocio)                               │  │
│  │  ├─ UserService: validar, expiración, hashing               │  │
│  │  ├─ DeviceService: registrar, asociar a usuario             │  │
│  │  ├─ RouterService: orquestar operaciones en router          │  │
│  │  ├─ ProfileService: asignar QoS                             │  │
│  │  ├─ DNSService: crear/eliminar bloqueos                     │  │
│  │  └─ DashboardService: calcular métricas en tiempo real      │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Models (Operaciones CRUD en BD)                            │  │
│  │  ├─ UserModel.create(), read(), update(), delete()          │  │
│  │  ├─ DeviceModel.create(), list(), update()                  │  │
│  │  ├─ SessionModel.insert_active(), get_history()             │  │
│  │  ├─ TrafficModel.insert_snapshot(), get_stats()             │  │
│  │  └─ AuditLogModel.insert(), list_paginated()                │  │
│  └─────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  RouterOS Client (routeros/client.py)                       │  │
│  │  HTTP Client async (httpx)                                  │  │
│  │                                                             │  │
│  │  Métodos:                                                   │  │
│  │  ├─ get_arp_table() → lee dispositivos activos              │  │
│  │  ├─ get_dhcp_leases() → leases activos                      │  │
│  │  ├─ add_mac_to_whitelist(mac)                               │  │
│  │  ├─ remove_mac_from_whitelist(mac)                          │  │
│  │  ├─ add_queue(name, target, limit)                          │  │
│  │  ├─ update_queue(name, limit)                               │  │
│  │  ├─ add_dns_entry(domain, address)                          │  │
│  │  ├─ get_queue_stats() → tráfico por dispositivo             │  │
│  │  └─ test_connection() → health check                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│         REST API del Router MikroTik (192.168.88.1:80)              │
│          /rest/ip/firewall/address-list (whitelist/blocklist)      │
│          /rest/queue/simple (QoS)                                   │
│          /rest/ip/dns/static (DNS bloqueados)                       │
│          /rest/ip/arp (dispositivos en red)                         │
│          /rest/ip/dhcp-server/lease (IPs asignadas)                │
├─────────────────────────────────────────────────────────────────────┤
│                    SQLite (data/db.sqlite3)                         │
│  ┌────────────┬──────────┬──────────┬────────────┬─────────────┐  │
│  │   users    │ devices  │ sessions │  traffic   │ audit_log   │  │
│  │ (operadores│ (MACs    │ (activas │ _snapshots │ (historial) │  │
│  │ y usuarios)│ registr.)│ y histo.)│(tráfico 5m)│             │  │
│  └────────────┴──────────┴──────────┴────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  APScheduler (scheduler/tasks.py)                           │  │
│  │  ├─ Cada 30s: Health check router                           │  │
│  │  ├─ Cada 1m: Lectura ARP + sesiones activas                 │  │
│  │  ├─ Cada 5m: Snapshot de tráfico (queue stats)              │  │
│  │  └─ Cada 10m: Verificar usuarios expirados                  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujos de datos

### 1. Login → Autenticación

```
┌─────────────────────┐
│  Usuario ingresa    │
│  username/password  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  POST /api/auth/login               │
│  Body: {username, password}         │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  AuthService.verify_credentials()   │
│  ├─ Buscar usuario en BD            │
│  ├─ Verificar password con bcrypt   │
│  └─ Generar JWT (24h exp)           │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Response: {token, user_info}       │
│  (token = JWT con rol incluido)     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Frontend guarda en localStorage:   │
│  localStorage.setItem('token', ...)│
└─────────────────────────────────────┘
```

### 2. Registrar usuario → Integración con router

```
┌──────────────────────────────┐
│ Operador llena formulario:   │
│ - Nombre                     │
│ - Cédula                     │
│ - Cargo                      │
│ - MAC address                │
│ - Perfil QoS                 │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  POST /api/users                     │
│  Headers: Authorization: Bearer {...}│
│  Body: {...user data, mac, profile}  │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Middleware JWT verifica token       │
│  ├─ Extrae claims (usuario, rol)     │
│  └─ Inyecta en request               │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Router endpoint /api/users          │
│  ├─ Valida con Pydantic              │
│  ├─ Verifica permisos (ADMIN_RED+)   │
│  └─ Llama UserService.create()       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  UserService.create()                │
│  ├─ Valida datos                     │
│  ├─ Hash contraseña (bcrypt)         │
│  ├─ Inserta en tabla users (BD)      │
│  ├─ Obtiene ID usuario               │
│  └─ Retorna usuario creado           │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  RouterService.register_device()     │
│  ├─ Llama RouterOSClient.add_mac_... │
│  │  POST /rest/ip/firewall/...       │
│  │  (agrega MAC a whitelist)         │
│  ├─ Llama RouterOSClient.create...   │
│  │  POST /rest/queue/simple          │
│  │  (crea cola QoS con perfil)       │
│  └─ Retorna operaciones realizadas   │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  AuditLog.insert()                   │
│  {operator_id, action: "register",   │
│   entity_type: "user", entity_id...} │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Response: {id, name, mac, status}   │
│  Status: 201 Created                 │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Frontend recibe y actualiza tabla   │
│  ✓ Usuario registrado en BD          │
│  ✓ MAC en whitelist del router       │
│  ✓ Cola QoS creada en router         │
└──────────────────────────────────────┘
```

### 3. Dashboard en tiempo real

```
┌─────────────────────┐
│  Página dashboard   │
│  carga             │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────┐
│  JavaScript polling              │
│  setInterval(() => {             │
│    fetch(/api/dashboard)         │
│  }, 30000)  // cada 30 segundos  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  GET /api/dashboard              │
│  Token en Authorization header   │
└──────────┬───────────────────────┘
           │
           ▼
┌───────────────────────────────────────┐
│  DashboardService.get_metrics()       │
│  ├─ RouterOSClient.get_arp_table()    │
│  │  HTTP GET /rest/ip/arp            │
│  ├─ RouterOSClient.get_queue_stats()  │
│  │  HTTP GET /rest/queue/simple       │
│  ├─ DeviceModel.list() → BD          │
│  ├─ SessionModel.get_active() → BD   │
│  └─ Cruza datos + calcula métricas   │
└──────────┬────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Response JSON:                      │
│  {                                   │
│    "total_registered": 42,           │
│    "active_now": 18,                 │
│    "top_devices": [...],             │
│    "unregistered_macs": [            │
│      {mac, bytes_in, bytes_out}      │
│    ],                                │
│    "router_latency_ms": 45           │
│  }                                   │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Frontend actualiza DOM:             │
│  ├─ Tabla de dispositivos            │
│  ├─ Gráficas de tráfico              │
│  ├─ Alertas (rojas)                  │
│  └─ Status del router                │
│                                      │
│  Siguiente polling en 30s...         │
└──────────────────────────────────────┘
```

### 4. Bloquear dispositivo

```
┌─────────────────────┐
│  Clic "Bloquear"    │
│  en tabla usuarios  │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────┐
│  PUT /api/users/{user_id}        │
│  Body: {status: "blocked"}       │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  UserService.update()            │
│  ├─ Actualiza BD (status)        │
│  ├─ Obtiene device del usuario   │
│  └─ Llama RouterService.block()  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  RouterService.block_device()    │
│  ├─ PATCH /rest/ip/firewall/...  │
│  │  (deshabilita en whitelist)   │
│  ├─ PATCH /rest/queue/simple/{id}│
│  │  (deshabilita cola QoS)       │
│  └─ MAC pierde acceso            │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  AuditLog.insert()               │
│  {action: "block", user_id...}   │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Response: 200 OK                │
│  ✓ Usuario bloqueado en BD       │
│  ✓ MAC en whitelist deshabilitada│
│  ✓ Cola QoS deshabilitada        │
│  → Dispositivo sin acceso        │
└──────────────────────────────────┘
```

---

## 🔐 Flujo de autenticación y autorización

```
Request HTTP
    │
    ▼
┌─────────────────────────────────────────┐
│  CORS Middleware                        │
│  ✓ Verifica origin permitido            │
└─────────────┬───────────────────────────┘
              │
              ▼
        ¿Es /api/auth/login?
              │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   └─ Verifica credenciales
         │   └─ Devuelve token JWT
         │
         ▼
┌─────────────────────────────────────────┐
│  JWT Middleware                         │
│  ├─ Extrae "Authorization: Bearer ..."  │
│  ├─ Verifica firma (SECRET_KEY)         │
│  ├─ Verifica expiración (24h)           │
│  ├─ Valida que no está en blacklist     │
│  └─ Inyecta usuario en request          │
└─────────────┬───────────────────────────┘
              │
              ▼
         ¿Token válido?
              │
         NO   │   SÍ
         │    │
         ▼    │
    401 Unauth
         │    │
         │    ▼
         │  ┌──────────────────────────────┐
         │  │  Roles Middleware            │
         │  │  Verifica rol del usuario:   │
         │  │  ├─ SUPERADMIN (acceso full) │
         │  │  ├─ ADMIN_RED (usuarios+)    │
         │  │  └─ SOPORTE (lectura)        │
         │  └──────────┬───────────────────┘
         │             │
         │             ▼
         │        ¿Rol permitido para
         │         este endpoint?
         │             │
         │        NO   │   SÍ
         │        │    │
         │        ▼    ▼
         │      403 Forbidden
         │             │
         └─────────────┴─────────────────▶ 200 OK
                                          (continúa)
```

---

## 🔄 Ciclo de vida de una sesión activa

```
Dispositivo se conecta al WiFi DS-1405-PDVSA
    │
    ▼
DHCP asigna IP (192.168.88.100-200)
    │
    ▼
APScheduler (cada 1 minuto):
    │
    ├─ GET /rest/ip/arp
    │  └─ Lee tabla ARP (MAC + IP del dispositivo)
    │
    ├─ GET /rest/ip/hotspot/active
    │  └─ Lee sesiones activas
    │
    └─ SessionModel.insert_active()
       └─ Guarda en tabla sessions
           {device_id, start_time, current_bytes...}
    │
    ▼
APScheduler (cada 5 minutos):
    │
    ├─ GET /rest/queue/simple
    │  └─ Lee estadísticas de tráfico por cola
    │
    └─ TrafficModel.insert_snapshot()
       └─ Guarda snapshot
           {device_id, timestamp, bytes_in, bytes_out}
    │
    ▼
Dashboard (polling cada 30s):
    │
    └─ GET /api/dashboard
       ├─ DashboardService cruza datos
       ├─ Calcula consumo actual
       └─ Muestra en tabla + gráficas
    │
    ▼
Dispositivo se desconecta
    │
    └─ SessionModel.finalize_session()
       └─ Cierra sesión en tabla
           {end_time, total_duration, total_bytes}
    │
    ▼
Historial persiste en BD
    └─ GET /api/history/{user_id}
       └─ Gráficas y reportes históricos
```

---

## 📡 Comunicación con RouterOS

### HTTP Method Mapping

```
READ operations:
GET /rest/ip/arp                        → Dispositivos en red
GET /rest/ip/hotspot/active             → Sesiones activas
GET /rest/ip/dhcp-server/lease          → Leases DHCP
GET /rest/queue/simple                  → Colas QoS
GET /rest/ip/firewall/address-list      → Listas (white/black)
GET /rest/ip/dns/static                 → Entradas DNS

WRITE operations (CREATE):
POST /rest/ip/firewall/address-list     → Agregar MAC a lista
POST /rest/queue/simple                 → Crear cola QoS
POST /rest/ip/dns/static                → Agregar bloqueo DNS

WRITE operations (UPDATE):
PATCH /rest/ip/firewall/address-list/{id} → Modificar entrada
PATCH /rest/queue/simple/{id}           → Actualizar límite
PATCH /rest/ip/dns/static/{id}          → Modificar entrada

WRITE operations (DELETE):
DELETE /rest/ip/firewall/address-list/{id} → Remover MAC
DELETE /rest/queue/simple/{id}          → Eliminar cola
DELETE /rest/ip/dns/static/{id}         → Remover bloqueo
```

### Autenticación REST API

```
Todos los requests usan HTTP Basic Auth:

Authorization: Basic base64(api-container:NAC_MikroTik_2025)

Ejemplo curl:
curl -u api-container:NAC_MikroTik_2025 \
     http://192.168.88.1:80/rest/ip/arp
```

---

## 🔄 Error handling

```
┌────────────────────────────┐
│  Request a endpoint        │
└────────────┬───────────────┘
             │
             ▼
    ¿Validación Pydantic?
             │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   ValidationError
         │       │
         │       ▼
         │   Response 422
         │   {
         │    "detail": [
         │      {
         │       "loc": ["body", "email"],
         │       "msg": "invalid email format",
         │       "type": "value_error"
         │      }
         │     ]
         │   }
         │
         ▼
    ¿Autenticación?
             │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   401 Unauthorized
         │   {
         │    "detail": "Invalid credentials"
         │   }
         │
         ▼
    ¿Autorización (rol)?
             │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   403 Forbidden
         │   {
         │    "detail": "Insufficient permissions"
         │   }
         │
         ▼
    ¿Recurso existe?
             │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   404 Not Found
         │   {
         │    "detail": "User not found"
         │   }
         │
         ▼
    ¿Operación en BD exitosa?
             │
        NO   │   SÍ
         ├───┘   │
         │       ▼
         │   500 Internal Server Error
         │   {
         │    "detail": "Database error"
         │   }
         │       │
         │       ▼
         │   200/201 OK
         │   {
         │    "id": 1,
         │    "name": "John",
         │    ...
         │   }
         │
         └───────┴──────────────────────▶ Response
```

---

## 📝 Resumen arquitectura

| Aspecto | Decisión |
|---|---|
| **Frontend** | HTML vanilla + JS vanilla (sin frameworks pesados) |
| **Backend** | FastAPI (async, rápido, validación automática) |
| **BD** | SQLite aiosqlite (local, no requiere servidor) |
| **Autenticación** | JWT en localStorage (stateless) |
| **Router** | httpx async (no bloquea, eficiente) |
| **Scheduler** | APScheduler (tareas periódicas) |
| **Servidor** | uvicorn (ASGI, soporta async) |
| **Errores** | Global exception handler + Pydantic validation |
| **Concurrencia** | AsyncIO (múltiples requests simultáneos) |
| **Seguridad** | Passwords hasheadas, JWT firmados, HTTPS verify=False |

---

**Documento completado: Arquitectura detallada y diagramas ✅**
