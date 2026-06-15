# 📁 ENTREGABLE 2: Estructura del Proyecto Python

**Estado:** ✅ COMPLETADO  
**Fecha:** 2025-06-11

---

## 🎯 Objetivo

Definir el layout completo de carpetas y archivos del proyecto NAC, con descripción detallada del rol de cada módulo.

---

## 📂 Árbol de directorios completo

```
miktotik/
├── app/                              # 📦 Aplicación principal
│   ├── __init__.py
│   ├── main.py                       # 🚀 Punto de entrada (FastAPI)
│   ├── config.py                     # ⚙️ Configuración y variables de entorno
│   ├── dependencies.py               # 🔗 Inyección de dependencias (sesión BD, auth)
│   │
│   ├── auth/                         # 🔐 Autenticación y autorización
│   │   ├── __init__.py
│   │   ├── schemas.py                # Pydantic: LoginRequest, TokenResponse
│   │   ├── models.py                 # Modelos: Usuario, Token
│   │   ├── service.py                # Lógica: hash password, generar JWT, validar token
│   │   └── security.py               # Funciones: crear token, verificar token
│   │
│   ├── routers/                      # 🛣️ Routers/Endpoints de la API
│   │   ├── __init__.py
│   │   ├── auth.py                   # POST /api/auth/login, logout, me
│   │   ├── users.py                  # CRUD usuarios: GET, POST, PUT, DELETE
│   │   ├── devices.py                # CRUD dispositivos: GET, POST, PUT, DELETE
│   │   ├── dashboard.py              # GET /api/dashboard (métricas en tiempo real)
│   │   ├── profiles.py               # GET/POST/PUT perfiles QoS
│   │   ├── dns.py                    # GET/POST/DELETE DNS categories y entries
│   │   ├── history.py                # GET historial de usuario, exportar CSV
│   │   ├── operators.py              # CRUD operadores (solo admin)
│   │   ├── audit.py                  # GET log de auditoría paginado
│   │   └── router_status.py          # GET health check del router
│   │
│   ├── schemas/                      # 📋 Esquemas Pydantic (validación)
│   │   ├── __init__.py
│   │   ├── user.py                   # UserCreate, UserUpdate, UserResponse
│   │   ├── device.py                 # DeviceCreate, DeviceResponse
│   │   ├── profile.py                # ProfileResponse
│   │   ├── dns.py                    # DNSCategoryResponse, DNSEntryResponse
│   │   ├── dashboard.py              # DashboardMetrics, DeviceStats
│   │   └── common.py                 # PaginatedResponse, ErrorResponse
│   │
│   ├── models/                       # 🗄️ Modelos y operaciones de BD
│   │   ├── __init__.py
│   │   ├── database.py               # Inicialización SQLite, conexión
│   │   ├── user.py                   # Tabla users: CRUD methods
│   │   ├── device.py                 # Tabla devices: CRUD methods
│   │   ├── operator.py               # Tabla operators: CRUD methods
│   │   ├── profile.py                # Tabla bandwidth_profiles
│   │   ├── session.py                # Tabla sessions: sesiones activas
│   │   ├── traffic.py                # Tabla traffic_snapshots: histórico tráfico
│   │   ├── dns_category.py           # Tabla dns_categories
│   │   ├── dns_entry.py              # Tabla dns_entries
│   │   ├── audit_log.py              # Tabla audit_log
│   │   └── router_sync.py            # Tabla router_sync_log
│   │
│   ├── services/                     # 🔧 Servicios y lógica de negocio
│   │   ├── __init__.py
│   │   ├── router_service.py         # Comunicación con RouterOS
│   │   ├── user_service.py           # Lógica de usuarios
│   │   ├── device_service.py         # Lógica de dispositivos
│   │   ├── profile_service.py        # Lógica de perfiles QoS
│   │   ├── dns_service.py            # Lógica de DNS
│   │   ├── dashboard_service.py      # Cálculo de métricas
│   │   └── sync_service.py           # Sincronización con router
│   │
│   └── middleware/                   # 🛡️ Middleware
│       ├── __init__.py
│       ├── auth.py                   # Verificación de JWT
│       ├── roles.py                  # Control de roles (SUPERADMIN, ADMIN_RED, SOPORTE)
│       └── error_handler.py          # Manejo global de errores
│
├── routeros/                         # 🔌 Cliente RouterOS (comunicación REST)
│   ├── __init__.py
│   ├── client.py                     # Clase RouterOSClient (httpx async)
│   ├── endpoints.py                  # Métodos para cada endpoint
│   ├── exceptions.py                 # Excepciones tipadas
│   ├── auth.py                       # Autenticación HTTP Basic
│   └── models.py                     # Data classes para respuestas
│
├── scheduler/                        # ⏱️ Tareas en background (APScheduler)
│   ├── __init__.py
│   ├── tasks.py                      # Funciones de tareas
│   └── scheduler.py                  # Inicialización APScheduler
│
├── static/                           # 🎨 Frontend (HTML, CSS, JS)
│   ├── index.html                    # Página principal (redirige a login)
│   ├── login.html                    # Formulario login
│   │
│   ├── pages/                        # Páginas principales
│   │   ├── dashboard.html            # Dashboard en tiempo real
│   │   ├── users.html                # Gestión de usuarios
│   │   ├── register.html             # Registro de nuevo usuario
│   │   ├── devices.html              # Gestión de dispositivos
│   │   ├── profiles.html             # Gestión de perfiles QoS
│   │   ├── dns.html                  # Gestión de DNS
│   │   ├── history.html              # Historial de usuario
│   │   ├── audit.html                # Log de auditoría
│   │   ├── operators.html            # Gestión de operadores (admin)
│   │   └── settings.html             # Configuración
│   │
│   ├── js/                           # JavaScript vanilla
│   │   ├── app.js                    # Inicialización y router
│   │   ├── api.js                    # Cliente HTTP (fetch)
│   │   ├── auth.js                   # Gestión de autenticación (JWT en localStorage)
│   │   ├── dashboard.js              # Lógica dashboard (polling, gráficas)
│   │   ├── users.js                  # CRUD usuarios (tablas, formularios)
│   │   ├── devices.js                # CRUD dispositivos
│   │   ├── profiles.js               # Gestión perfiles
│   │   ├── dns.js                    # Gestión DNS
│   │   ├── history.js                # Gráficas históricas, export CSV
│   │   ├── audit.js                  # Log auditoría (paginación)
│   │   ├── utils.js                  # Funciones auxiliares (formateo, validación)
│   │   └── components.js             # Componentes reutilizables (modal, table, form)
│   │
│   ├── css/                          # Estilos
│   │   ├── style.css                 # Estilos globales
│   │   ├── responsive.css            # Media queries (mobile, tablet)
│   │   ├── theme.css                 # Variables CSS (colores, tipografía)
│   │   └── components.css            # Estilos componentes
│   │
│   └── lib/                          # Librerías externas (CDN)
│       └── alpine.js                 # (Opcional) Alpine.js para reactividad
│
├── data/                             # 💾 Almacenamiento local
│   ├── db.sqlite3                    # Base de datos SQLite
│   ├── nac-1.0.tar.xz                # Backup anterior (ignorar)
│   └── backups/                      # Backups de BD
│
├── tests/                            # 🧪 Tests unitarios
│   ├── __init__.py
│   ├── test_auth.py                  # Tests autenticación
│   ├── test_users.py                 # Tests CRUD usuarios
│   ├── test_devices.py               # Tests CRUD dispositivos
│   ├── test_router_client.py         # Tests cliente RouterOS (mocks)
│   ├── test_services.py              # Tests lógica de negocio
│   └── conftest.py                   # Fixtures pytest
│
├── logs/                             # 📜 Logs de la aplicación
│   ├── app.log
│   └── router_sync.log
│
├── docs/                             # 📚 Documentación adicional
│   ├── API.md                        # Especificación OpenAPI/Swagger
│   ├── DATABASE.md                   # Esquema de BD
│   ├── DEPLOYMENT.md                 # Instrucciones de despliegue
│   └── TROUBLESHOOTING.md            # Solución de problemas
│
├── .env.example                      # 📝 Template de variables
├── .env                              # 🔒 Variables de entorno (no commitear)
├── .gitignore                        # Exclusiones git
├── requirements.txt                  # Dependencias Python
├── pyproject.toml                    # (Opcional) Configuración proyecto
│
├── install.sh                        # 🚀 Script instalación (Linux/Mac)
├── install.bat                       # 🚀 Script instalación (Windows)
│
├── main.py                           # Punto de entrada alternativo
├── docker-compose.yml                # (Opcional) Orquestación
├── Dockerfile                        # Containerización
│
├── venv/                             # Virtual environment (no commitear)
├── __pycache__/                      # Cache Python (no commitear)
│
├── PROGRESO.md                       # 📈 Documento de avance (actualizar)
├── COMIENZA_AQUI.md                  # 👈 Punto de entrada
├── QUICK_START_ROUTER.md
├── ROUTER_SETUP.md
├── PROYECTO.md                       # 👈 Este archivo
├── ARQUITECTURA.md                   # Diagrama de arquitectura
│
└── README.md                         # Readme principal (actualizar)
```

---

## 📋 Descripción de módulos principales

### `app/main.py` — Punto de entrada de FastAPI
**Responsabilidad:** Inicializar aplicación, registrar routers, configurar middleware

```
- Crear aplicación FastAPI
- Configurar CORS
- Registrar routers (/api/auth, /api/users, etc.)
- Servir archivos estáticos (frontend)
- Health check
- Global exception handler
```

### `app/config.py` — Configuración
**Responsabilidad:** Cargar variables de entorno y configuración

```
- Leer .env
- Validar variables obligatorias
- Proveer configuración a la app
- Configuración de logging
```

### `app/dependencies.py` — Inyección de dependencias
**Responsabilidad:** Proveer dependencias a los routers

```
- Sesión de BD
- Usuario autenticado (JWT)
- Cliente RouterOS
- Servicios
```

### `app/auth/*` — Autenticación y autorización
**Responsabilidad:** JWT, hashing de contraseñas, verificación de roles

```
- Generar JWT (login)
- Verificar JWT (protected routes)
- Hash de contraseñas (bcrypt)
- Control de roles (SUPERADMIN, ADMIN_RED, SOPORTE)
```

### `app/routers/*` — Endpoints de la API
**Responsabilidad:** Definir todos los endpoints REST

**Ejemplos:**
```
POST   /api/auth/login              — Login
POST   /api/auth/logout             — Logout
GET    /api/auth/me                 — Usuario actual

GET    /api/users                   — Listar usuarios (paginado)
POST   /api/users                   — Crear usuario
GET    /api/users/{id}              — Obtener usuario
PUT    /api/users/{id}              — Actualizar usuario
DELETE /api/users/{id}              — Eliminar usuario

GET    /api/devices                 — Listar dispositivos
POST   /api/devices                 — Registrar dispositivo
GET    /api/devices/live            — MACs visibles en la red (ARP)
PUT    /api/devices/{id}            — Actualizar dispositivo

GET    /api/dashboard               — Métricas en tiempo real
GET    /api/dashboard/active-now    — Dispositivos activos ahora
GET    /api/dashboard/alerts        — Alertas

POST   /api/profiles                — Crear perfil QoS
GET    /api/profiles                — Listar perfiles
PUT    /api/profiles/{id}           — Actualizar perfil

GET    /api/dns/categories          — Listar categorías DNS
POST   /api/dns/categories          — Crear categoría
GET    /api/dns/entries             — Listar entradas bloqueadas
POST   /api/dns/entries             — Agregar bloqueo

GET    /api/history/{user_id}       — Historial de usuario
GET    /api/history/{user_id}/csv   — Exportar CSV

GET    /api/audit                   — Log de auditoría (paginado)

GET    /api/operators               — Listar operadores (admin)
POST   /api/operators               — Crear operador (admin)

GET    /api/router/status           — Health check del router
```

### `app/schemas/*` — Validación Pydantic
**Responsabilidad:** Definir y validar estructura de datos (request/response)

```
- UserCreate, UserUpdate, UserResponse
- DeviceCreate, DeviceResponse
- LoginRequest, TokenResponse
- Errores validación automáticos
```

### `app/models/*` — Base de datos
**Responsabilidad:** Operaciones CRUD en SQLite

```
- Crear tablas
- Insertar, actualizar, eliminar registros
- Consultas (búsqueda, filtrado, paginación)
- Índices y relaciones
```

### `app/services/*` — Lógica de negocio
**Responsabilidad:** Orquestar operaciones complejas

```
- router_service: Comunicación con RouterOS
- user_service: Validar usuario, expiración, etc.
- device_service: Registrar dispositivo, asociar a usuario
- profile_service: Asignar perfil QoS
- dns_service: Crear/eliminar bloqueos DNS
- dashboard_service: Calcular métricas
```

### `routeros/client.py` — Cliente RouterOS
**Responsabilidad:** Comunicación REST con el router

```
- Conexión HTTPx async
- Métodos para cada endpoint:
  - get_arp_table()
  - get_dhcp_leases()
  - add_mac_to_whitelist()
  - add_queue()
  - add_dns_entry()
  - etc.
- Manejo de errores (401, 404, 500)
```

### `scheduler/tasks.py` — Tareas en background
**Responsabilidad:** Sincronización periódica con el router

```
- Cada 5 min: Snapshot de tráfico (traffic_snapshots)
- Cada 1 min: Lectura ARP y sesiones activas
- Cada 10 min: Verificar usuarios expirados (deshabilitar en router)
- Cada 60 seg: Health check del router
```

### `static/*` — Frontend
**Responsabilidad:** Interfaz de usuario web

**Páginas:**
```
login.html          → Formulario login
dashboard.html      → Métricas en tiempo real (polling 30s)
users.html          → CRUD usuarios (tabla con búsqueda/filtros)
register.html       → Formulario registro (selector de MACs live)
devices.html        → Gestión de dispositivos
profiles.html       → Gestión perfiles QoS
dns.html            → Gestión DNS (categorías y dominios)
history.html        → Gráfica de consumo + tabla de sesiones
audit.html          → Log de auditoría (paginado)
operators.html      → Gestión operadores (solo admin)
```

**Tecnología:**
```
- HTML5 vanilla
- CSS3 sin frameworks (responsive, mobile-first)
- JavaScript vanilla con fetch()
- Alpine.js opcional para reactividad simple
- Gráficas: Chart.js (ligero) o similar
```

---

## 🔗 Relaciones entre módulos

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUARIO (Navegador)                       │
├─────────────────────────────────────────────────────────────────┤
│                          Frontend                                │
│  static/pages/ (HTML) + static/js/ (JavaScript) + static/css/  │
├─────────────────────────────────────────────────────────────────┤
│                    Fetch → /api/...                             │
├─────────────────────────────────────────────────────────────────┤
│                      FastAPI App                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  main.py (FastAPI) + Middleware (auth, roles)            │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │  Routers                                                 │ │
│  │  auth.py, users.py, devices.py, dashboard.py, etc.      │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │  Services                                                │ │
│  │  Lógica de negocio (user_service, device_service, etc.) │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │  Models (BD)                                             │ │
│  │  CRUD a SQLite                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    routeros/client.py                           │
│             HTTP REST ↔ RouterOS (192.168.88.1:80)             │
├─────────────────────────────────────────────────────────────────┤
│                      data/db.sqlite3                            │
│         (users, devices, audit_log, traffic_snapshots)         │
├─────────────────────────────────────────────────────────────────┤
│                  scheduler/tasks.py                             │
│            APScheduler (tareas en background)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Tablas de base de datos

### users
```sql
id, username, password_hash, full_name, email, phone, role, created_at, updated_at
```

### devices
```sql
id, mac_address, device_name, device_type, user_id, profile_id, 
status (active/suspended/expired), assigned_ip, created_at, updated_at
```

### operators
```sql
id, username, password_hash, role (SUPERADMIN/ADMIN_RED/SOPORTE), 
created_by, created_at, last_login
```

### bandwidth_profiles
```sql
id, name, max_upload, max_download, priority, created_at
Registros: ADMIN, PROFESIONAL, ESTANDAR, INVITADO
```

### sessions
```sql
id, device_id, start_time, end_time, uptime, bytes_in, bytes_out
Sesiones activas/históricas
```

### traffic_snapshots
```sql
id, device_id, timestamp, bytes_in, bytes_out, packets
Toma snapshot cada 5 minutos
```

### dns_categories
```sql
id, name, description
Registros: redes_sociales, streaming, juegos, noticias, adultos, custom
```

### dns_entries
```sql
id, category_id, domain, address (0.0.0.0)
Dominios bloqueados
```

### audit_log
```sql
id, operator_id, action (register/suspend/block/unblock/update), 
entity_type (user/device/dns), entity_id, result (success/failure), 
timestamp, details
```

### router_sync_log
```sql
id, timestamp, action, status (success/failure), message, latency_ms
Health checks del router
```

---

## 🔒 Roles y permisos

### SUPERADMIN
```
✓ Gestionar usuarios
✓ Gestionar dispositivos
✓ Gestionar perfiles QoS
✓ Gestionar DNS
✓ Ver historial y auditoría
✓ Gestionar operadores
✓ Ver estado del router
```

### ADMIN_RED
```
✓ Gestionar usuarios
✓ Gestionar dispositivos
✓ Cambiar perfiles QoS
✓ Gestionar DNS
✓ Ver historial
✓ Ver estado del router
✗ Gestionar operadores (solo SUPERADMIN)
```

### SOPORTE
```
✓ Ver usuarios (solo lectura)
✓ Ver dispositivos (solo lectura)
✓ Ver estado del router
✗ Crear/modificar/eliminar
✗ Gestionar perfiles
```

---

## 📊 Flujos principales

### Registro de usuario (flujo completo)
```
1. Operador accede a /register
2. Sistema lee ARP del router (MACs visibles)
3. Operador selecciona MAC + datos usuario
4. POST /api/users
5. Service crea usuario en BD
6. Service: POST a /rest/ip/firewall/address-list (whitelist en router)
7. Service: POST a /rest/queue/simple (cola QoS en router)
8. Response con usuario creado
9. Audit log: "Registro usuario {nombre} MAC {mac}"
```

### Login
```
1. Usuario/operador accede a /login
2. POST /api/auth/login (username, password)
3. Backend verifica contraseña
4. Genera JWT (exp: 24 horas)
5. Response: token en JSON
6. Frontend guarda token en localStorage
7. Siguientes requests incluyen "Authorization: Bearer {token}"
```

### Dashboard en tiempo real
```
1. Página dashboard.html carga
2. JavaScript polling cada 30 segundos
3. GET /api/dashboard
4. Backend:
   - Lee /rest/ip/arp (dispositivos activos)
   - Lee /rest/queue/simple (tráfico)
   - Cruza con BD (usuarios registrados)
   - Calcula métricas
5. Response: JSON con métricas
6. Frontend actualiza tabla/gráficas
```

### Bloquear dispositivo
```
1. Operador selecciona usuario en tabla
2. Click "Bloquear"
3. PUT /api/users/{id} (status=blocked)
4. Service:
   - Actualiza BD
   - PATCH /rest/ip/firewall/address-list (disable whitelist)
   - PATCH /rest/queue/simple (disable cola)
5. Audit log: "Bloqueado {user}"
6. Dispositivo pierde acceso inmediatamente
```

---

## 🚀 Stack tecnológico resumido

| Capa | Componente | Tecnología |
|---|---|---|
| **Frontend** | UI | HTML5, CSS3, JavaScript vanilla |
| **Frontend** | Libs | Alpine.js (opcional), Chart.js (gráficas) |
| **Backend** | Framework | FastAPI |
| **Backend** | Async | AsyncIO, httpx |
| **BD** | Sistema | SQLite (aiosqlite) |
| **Autenticación** | JWT | python-jose, bcrypt |
| **Validación** | Schemas | Pydantic |
| **Router** | Cliente REST | httpx (async) |
| **Scheduler** | Tareas | APScheduler |
| **Web** | Server | uvicorn |
| **Containerización** | Docker | Dockerfile, docker-compose |

---

## 📈 Próximos pasos

1. **Entregable 2** (este): ✅ Estructura completada
2. **Entregable 3**: Cliente RouterOS (`routeros/client.py`)
3. **Entregable 4**: Modelos SQLite (`app/models/*`)
4. **Entregable 5**: Backend FastAPI (`app/routers/*` + `app/services/*`)
5. **Entregable 6**: Frontend (`static/*`)
6. **Entregable 7**: Scheduler (`scheduler/tasks.py`)
7. **Entregable 8**: Instalación y deployment

---

**Documento completado:** Estructura del proyecto definida y documentada ✅
