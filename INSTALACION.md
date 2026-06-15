# 📦 Guía de Instalación - MikroTik NAC System

## 🚀 Requisitos Previos

- **Python 3.9+** (recomendado 3.11 o superior)
- **pip** (gestor de paquetes de Python)
- **Router MikroTik** con RouterOS 7.x+
- **Windows 10/11 o Linux** (PC local)
- **Conexión de red** al router

## 1️⃣ Instalación en Windows

### Paso 1: Descargar e Instalar Python

1. Ir a [python.org](https://www.python.org/downloads/)
2. Descargar Python 3.11+ (Windows installer)
3. Ejecutar instalador
4. ✅ **Marcar: "Add Python to PATH"**
5. Completar instalación

### Paso 2: Clonar o Descargar el Proyecto

```bash
# Opción A: Con Git (si está instalado)
git clone <url-del-repo>
cd miktotik

# Opción B: Descargar ZIP y extraer
# Luego abrir CMD en la carpeta del proyecto
```

### Paso 3: Crear Ambiente Virtual

```bash
# Crear ambiente virtual
python -m venv venv

# Activar ambiente virtual
venv\Scripts\activate

# Deberías ver (venv) en el prompt
```

### Paso 4: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 5: Configurar Variables de Entorno

```bash
# Copiar template
copy .env.example .env

# Editar .env con Notepad
notepad .env
```

Editar estos valores:
```ini
ROUTER_IP=192.168.88.1
ROUTER_USER=api-container
ROUTER_PASSWORD=tu_contraseña
SECRET_KEY=tu_clave_secreta_generada
```

### Paso 6: Inicializar Base de Datos

```bash
# La BD se crea automáticamente, pero verifica:
python -c "from app.models import init_db; import asyncio; asyncio.run(init_db())"
```

### Paso 7: Iniciar la Aplicación

```bash
# Asegurar que el ambiente virtual está activado
# (venv) debe estar en el prompt

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Output esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete
```

### Paso 8: Acceder a la Aplicación

Abrir navegador:
```
http://localhost:8080
```

---

## 2️⃣ Instalación en Linux

### Paso 1: Instalar Python y Dependencias

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.11 python3-pip
```

### Paso 2: Clonar Proyecto

```bash
git clone <url-del-repo>
cd miktotik
```

### Paso 3: Crear Ambiente Virtual

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Paso 4: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 5: Configurar Variables

```bash
cp .env.example .env
nano .env  # o vim .env
```

Editar valores de router y contraseña.

### Paso 6: Iniciar Aplicación

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

---

## 3️⃣ Instalación en macOS

### Paso 1: Instalar Python (si no está)

```bash
# Con Homebrew
brew install python@3.11

# Verificar
python3 --version
```

### Paso 2: Clonar Proyecto

```bash
git clone <url-del-repo>
cd miktotik
```

### Paso 3: Crear Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 4: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 5: Configurar Variables

```bash
cp .env.example .env
vim .env
```

### Paso 6: Iniciar Aplicación

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

---

## 🐳 Instalación con Docker (Opcional)

### Paso 1: Instalar Docker

- Descargar [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Instalar y reiniciar

### Paso 2: Crear Dockerfile

Crear archivo `Dockerfile` en la raíz:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Paso 3: Construir Imagen

```bash
docker build -t miktotik-nac:latest .
```

### Paso 4: Ejecutar Contenedor

```bash
docker run -p 8080:8080 \
  -e ROUTER_IP=192.168.88.1 \
  -e ROUTER_USER=api-container \
  -e ROUTER_PASSWORD=contraseña \
  -v nac-data:/data \
  miktotik-nac:latest
```

---

## ⚙️ Configuración del Router

### Preparar Router MikroTik

Ejecutar script de configuración (ya incluido en `routeros/router_setup.rsc`):

```bash
# En Windows
python app\configure_router.py

# En Linux/macOS
python app/configure_router.py
```

Este script:
- ✅ Habilita REST API
- ✅ Crea usuario `api-container`
- ✅ Configura firewall
- ✅ Prepara address-lists (whitelist/blacklist)
- ✅ Configura DNS estático

---

## 🔐 Crear Primer Usuario

### Opción A: Via API (Recomendado)

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "contraseña"}'
```

### Opción B: Acceder a la BD Directamente

```bash
# Abrir BD SQLite
sqlite3 data/db.sqlite3

# Insertar usuario admin
INSERT INTO users (username, password_hash, full_name, role)
VALUES ('admin', 'hashed_password', 'Administrador', 'SUPERADMIN');
```

---

## 🚀 Ejecución en Producción

### Con Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080 \
  --timeout 120
```

### Con Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Con Supervisor (Auto-restart)

Crear `/etc/supervisor/conf.d/nac.conf`:

```ini
[program:nac-system]
command=/home/user/miktotik/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
directory=/home/user/miktotik
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/nac.err.log
stdout_logfile=/var/log/nac.out.log
```

Luego:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nac-system
```

---

## 🧪 Verificar Instalación

### Verificar Python

```bash
python --version
# Debe mostrar Python 3.9+
```

### Verificar Ambiente Virtual

```bash
# Windows
where python  # Debe estar en venv\

# Linux/macOS
which python  # Debe estar en venv/bin/
```

### Verificar Dependencias

```bash
pip list
# Debe mostrar fastapi, uvicorn, aiosqlite, etc.
```

### Verificar Conexión al Router

```bash
python -c "from app.routeros import RouterOSClient; print('RouterOS client OK')"
```

### Verificar API

```bash
curl http://localhost:8080/health
# Debe retornar: {"status": "ok", "version": "1.0.0"}
```

---

## 📋 Estructura de Carpetas Esperada

```
miktotik/
├── app/
│   ├── models/
│   ├── routers/
│   ├── services/
│   ├── schemas/
│   ├── scheduler/
│   ├── auth/
│   ├── config.py
│   ├── main.py
│   └── dependencies.py
├── routeros/
├── static/
│   ├── js/
│   ├── css/
│   └── index.html
├── docs/
├── data/
│   └── db.sqlite3
├── .env
├── requirements.txt
└── README.md
```

---

## ✅ Checklist de Instalación

- [ ] Python 3.9+ instalado
- [ ] Ambiente virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` configurado con credenciales
- [ ] Router RouterOS preparado (script ejecutado)
- [ ] Base de datos inicializada
- [ ] Aplicación inicia sin errores
- [ ] Puedo acceder a `http://localhost:8080`
- [ ] Login funciona
- [ ] Dashboard muestra métricas

Si algo falla, ver sección de **Troubleshooting**.

---

## 🆘 Soporte

Para problemas comunes, ver: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Para documentación técnica, ver: 
- [ARQUITECTURA.md](docs/ARQUITECTURA.md)
- [SCHEDULER.md](docs/SCHEDULER.md)
- [ROUTEROS_CLIENT.md](docs/ROUTEROS_CLIENT.md)
