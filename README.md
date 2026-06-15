# 🔐 MikroTik NAC System

**Network Access Control para MikroTik RouterOS**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/adrpinto83/nac)

---

## 📋 Descripción

Sistema de Control de Acceso a Red (NAC) para gestionar dispositivos conectados a un MikroTik RouterOS. Proporciona:

- ✅ **Gestión de Usuarios** - Registro y control de acceso
- ✅ **Control de Dispositivos** - Whitelist/Blacklist de MACs
- ✅ **Monitoreo en Tiempo Real** - Dispositivos conectados
- ✅ **Load Balancing + Failover** - Múltiples ISPs
- ✅ **Control de QoS** - Límites de ancho de banda
- ✅ **Auditoría** - Log completo de acciones
- ✅ **Dashboard Moderno** - Interfaz intuitiva

---

## 🚀 Características

### Core
- FastAPI con autenticación JWT
- SQLite para persistencia
- Comunicación bidireccional con MikroTik via REST API
- Sincronización automática de dispositivos
- Scheduler de tareas periódicas

### Seguridad
- JWT tokens con expiración configurable
- Passwords hasheados con bcrypt
- CORS configurado
- Validación con Pydantic

### Escalabilidad
- Ready para producción
- Deployment en Railway con un click
- Dockerizado
- Variables de entorno configurables

---

## 📦 Requisitos

- Python 3.12+
- MikroTik RouterOS (hAP ac3 u similar)
- Conexión de red al router

---

## 🛠️ Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/adrpinto83/nac.git
cd nac
```

### 2. Crear virtualenv
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores
```

### 5. Iniciar la aplicación
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Acceder a:** `http://localhost:8080`

---

## 🚀 Deployment en Railway

### Opción 1: Automática (Recomendado)
Click en el botón [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/adrpinto83/nac) arriba

### Opción 2: Manual
1. Ir a [railway.app](https://railway.app)
2. Crear nuevo proyecto
3. Conectar repositorio GitHub
4. Railway detectará automáticamente la configuración
5. Deployal se inicia automáticamente

### Variables de Entorno en Railway
En Railway Dashboard:
1. Ir a Variables
2. Agregar:
   - `ROUTER_IP` - IP del router (ej: 192.168.88.1)
   - `SECRET_KEY` - Clave secreta aleatoria (usar `openssl rand -hex 32`)
   - Otras variables según `.env.example`

---

## 📚 Uso

### Login
```
Usuario: admin
Contraseña: admin123
```

### API Endpoints

#### Autenticación
```
POST   /api/auth/login      - Obtener JWT token
GET    /api/auth/me         - Info del usuario actual
POST   /api/auth/logout     - Cerrar sesión
```

#### Usuarios
```
GET    /api/users/          - Listar usuarios
POST   /api/users/          - Crear usuario
GET    /api/users/{id}      - Obtener usuario
PUT    /api/users/{id}      - Actualizar usuario
DELETE /api/users/{id}      - Eliminar usuario
```

#### Dispositivos
```
GET    /api/devices/live    - Dispositivos conectados (CRÍTICO)
GET    /api/devices/        - Listar dispositivos
POST   /api/devices/register - Registrar dispositivo
DELETE /api/devices/{id}    - Eliminar dispositivo
POST   /api/devices/{id}/block   - Bloquear dispositivo
POST   /api/devices/{id}/unblock - Desbloquear dispositivo
```

#### Dashboard
```
GET    /api/dashboard/metrics      - Métricas generales
GET    /api/dashboard/top-devices  - Top consumidores
GET    /api/dashboard/alerts       - Alertas del sistema
```

### Documentación Interactiva
Acceder a `/docs` para Swagger UI o `/redoc` para ReDoc

---

## 🔧 Configuración del Router MikroTik

### Requisitos
- Router con RouterOS v7+
- Acceso administrativo
- Puertos 1-2 para ISPs
- Puertos 3-4 para Access Points
- Puerto 5 para administración local

### Configuración automática
La configuración se aplica automáticamente via REST API durante el setup inicial.

**Arquitectura:**
```
ISP1 → Puerto 1 (DHCP WAN) ─┐
                             ├─→ Load Balancing
ISP2 → Puerto 2 (DHCP WAN) ─┤   + Failover
                             └─→ Masquerade NAT

APs  → Puertos 3,4 (DHCP LAN: 192.168.88.0/24)
Admin → Puerto 5 (IP: 192.168.88.5/24)
```

---

## 📊 Estructura del Proyecto

```
nac/
├── app/
│   ├── main.py             # Entrada de FastAPI
│   ├── config.py           # Configuración
│   ├── dependencies.py     # Inyección de dependencias
│   ├── models/             # Modelos de BD
│   ├── routers/            # Endpoints API
│   ├── schemas/            # Esquemas Pydantic
│   ├── services/           # Servicios de lógica
│   │   └── mikrotik_client.py  # Cliente REST MikroTik
│   ├── auth/               # Autenticación JWT
│   └── scheduler/          # Tareas periódicas
├── static/                 # Frontend (HTML/CSS/JS)
├── data/                   # Base de datos SQLite
├── requirements.txt        # Dependencias Python
├── Dockerfile              # Imagen Docker
├── Procfile                # Proceso para Railway
├── railway.json            # Config Railway
└── .env.example            # Variables de ejemplo
```

---

## 🔄 Integración con MikroTik

### Cliente REST
Ubicado en `app/services/mikrotik_client.py`

```python
async with MikroTikClient() as router:
    devices = await router.get_connected_devices()
    isp_status = await router.get_isp_status()
```

### Endpoints del Router Utilizados
- `/rest/ip/dhcp-server/lease` - Dispositivos conectados
- `/rest/ip/dhcp-client` - Estado ISPs
- `/rest/ip/firewall/address-list` - Whitelist/Blacklist
- `/rest/queue/simple` - Límites QoS
- `/rest/ip/route` - Rutas activas

---

## 📖 Documentación Adicional

- [INTEGRACION_API_ROUTER.md](./INTEGRACION_API_ROUTER.md) - Guía de API del router
- [ROUTER_INTEGRATION_CHECKLIST.md](./ROUTER_INTEGRATION_CHECKLIST.md) - Checklist de integración
- [PRUEBA_ENDPOINTS_RESULTADO.md](./PRUEBA_ENDPOINTS_RESULTADO.md) - Resultados de pruebas

---

## 🐛 Troubleshooting

### Error: "Router API connection failed"
- Verificar IP del router: `ping 192.168.88.1`
- Verificar puerto REST API: `telnet 192.168.88.1 8728`
- Verificar credenciales en `.env`

### Error: "Authentication failed"
- Usuario por defecto: `admin`
- Sin contraseña (router factory reset)
- Crear usuario en BD si es necesario

### Error: "Database locked"
- Cerrar otras instancias de la app
- Borrar `data/db.sqlite3` para reinicializar

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crear rama para tu feature
3. Commit cambios
4. Push a la rama
5. Abrir Pull Request

---

## 📝 Licencia

MIT License - ver LICENSE file

---

## 👤 Autor

**Adrian Pinto**
- GitHub: [@adrpinto83](https://github.com/adrpinto83)
- Email: adrpinto@gmail.com

---

## 🔗 Links

- **Repository:** https://github.com/adrpinto83/nac
- **Issues:** https://github.com/adrpinto83/nac/issues
- **Discussions:** https://github.com/adrpinto83/nac/discussions

---

## 📞 Soporte

Para preguntas o problemas:
1. Abrir un Issue en GitHub
2. Ver documentación en el repositorio
3. Revisar los ejemplos incluidos

---

**¡Gracias por usar MikroTik NAC System!** 🎉
