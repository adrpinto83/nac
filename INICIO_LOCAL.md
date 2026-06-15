# 🚀 Iniciar Sistema MikroTik NAC Localmente

## Estado de la Aplicación

✅ **Estructura**: Completamente lista  
✅ **Dependencias**: Instaladas en virtualenv  
✅ **Frontend**: Configurado correctamente  
✅ **Backend**: FastAPI con todos los endpoints  
✅ **Router API**: Configurado para conectarse a 192.168.88.1  

---

## Opción 1: Ejecutar con Script (RECOMENDADO)

```bash
./run.sh
```

El script automáticamente:
- Activa el virtualenv
- Crea directorios necesarios (data/, logs/)
- Inicia el servidor en puerto 8080

---

## Opción 2: Ejecutar Manualmente

```bash
# Activar virtualenv
source venv/bin/activate

# Crear directorios si no existen
mkdir -p data logs

# Iniciar servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

---

## 📍 Acceso a la Aplicación

| Componente | URL |
|-----------|-----|
| **Dashboard** | http://localhost:8080 |
| **API Docs** | http://localhost:8080/docs |
| **OpenAPI Spec** | http://localhost:8080/openapi.json |
| **Health Check** | http://localhost:8080/health |

---

## 🔗 Endpoints API Disponibles

### Autenticación
- `POST /api/auth/login` — Login de usuario
- `GET /api/auth/me` — Información del usuario actual
- `POST /api/auth/logout` — Logout
- `POST /api/auth/operators` — Crear operador (admin)

### Usuarios
- `GET /api/users/` — Listar usuarios
- `POST /api/users/` — Crear usuario
- `GET /api/users/{user_id}` — Obtener usuario
- `PUT /api/users/{user_id}` — Actualizar usuario
- `DELETE /api/users/{user_id}` — Eliminar usuario
- `POST /api/users/{user_id}/suspend` — Suspender usuario
- `POST /api/users/{user_id}/activate` — Activar usuario

### Dispositivos
- `GET /api/devices/` — Listar dispositivos
- `POST /api/devices/register` — Registrar dispositivo
- `GET /api/devices/live` — Dispositivos en línea (ARP)
- `POST /api/devices/{device_id}/block` — Bloquear dispositivo
- `POST /api/devices/{device_id}/unblock` — Desbloquear dispositivo
- `DELETE /api/devices/{device_id}` — Eliminar dispositivo

### Dashboard
- `GET /api/dashboard/metrics` — Métricas generales
- `GET /api/dashboard/top-devices` — Top dispositivos
- `GET /api/dashboard/alerts` — Alertas del sistema
- `GET /api/dashboard/network-stats` — Estadísticas de red

### Perfiles QoS
- `GET /api/profiles/` — Listar perfiles
- `POST /api/profiles/` — Crear perfil
- `PUT /api/profiles/{profile_id}` — Actualizar perfil

### DNS
- `GET /api/dns/categories` — Listar categorías DNS
- `POST /api/dns/categories` — Crear categoría
- `GET /api/dns/entries` — Listar entradas DNS
- `POST /api/dns/entries` — Crear entrada DNS
- `DELETE /api/dns/entries/{entry_id}` — Eliminar entrada DNS

### Estadísticas
- `GET /api/stats/dashboard` — Stats del dashboard

---

## 🔧 Configuración del Router

El sistema se conecta al router MikroTik via API REST en:

```
IP: 192.168.88.1
Puerto: 443 (HTTPS) o 80 (HTTP)
Usuario: api-container
Contraseña: NAC_MikroTik_2025
```

Configurado en: `.env`

---

## 📂 Estructura de Carpetas

```
/home/adrpinto/miktotik/
├── app/
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── config.py               # Configuración
│   ├── dependencies.py         # Inyección de dependencias
│   ├── models/                 # Modelos SQLite
│   ├── routers/                # Rutas API
│   ├── schemas/                # Esquemas Pydantic
│   ├── services/               # Servicios de lógica
│   ├── scheduler/              # Tareas periódicas
│   └── auth/                   # Autenticación JWT
├── static/                     # Frontend (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   ├── api.js
│   └── js/                     # Módulos JavaScript
├── data/                       # Base de datos SQLite
│   └── db.sqlite3
├── logs/                       # Logs de la aplicación
├── .env                        # Variables de entorno
├── run.sh                      # Script para ejecutar
└── requirements.txt            # Dependencias Python
```

---

## ✅ Checklist de Primer Inicio

- [ ] Router MikroTik conectado y accesible en 192.168.88.1
- [ ] PC conectada via Ethernet al router
- [ ] Ejecutar: `./run.sh` o comando manual
- [ ] Esperar a que aparezca: `INFO: Uvicorn running on http://0.0.0.0:8080`
- [ ] Abrir navegador: http://localhost:8080
- [ ] Login con credenciales (crear admin si es primera vez)
- [ ] Ver dashboard
- [ ] Revisar `/docs` para probar endpoints

---

## 🐛 Troubleshooting

### "Error: Connection refused to router"
- Verificar que router esté en 192.168.88.1
- Ping: `ping 192.168.88.1`
- Revisar .env: ROUTER_IP debe ser correcto

### "Error: Port 8080 already in use"
```bash
# Cambiar puerto en command
python -m uvicorn app.main:app --port 8081 --reload
```

### "Database locked"
- Cerrar otras instancias de la app
- O borrar data/db.sqlite3 y recrearla

### Frontend no carga CSS/JS
- Revisar que `/static` esté montado en FastAPI
- Ver console del navegador (F12) para errores

---

## 📝 Notas

- La app guarda datos en `data/db.sqlite3` (SQLite)
- Los logs se guardan en `logs/`
- Cambios en routers se recargan automáticamente (--reload)
- El JWT expira cada 24 horas (configurable en .env)

---

¿Dudas? Revisar documentación en:
- `ARQUITECTURA.md` — Diagramas y flujos
- `PROYECTO.md` — Estructura detallada
- `.env` — Variables configurables
