# 📤 Guía: Subir a GitHub y Desplegar en Railway

## Paso 1: Crear Repositorio en GitHub

### 1.1 Ir a GitHub
```
https://github.com/new
```

### 1.2 Configurar Repositorio
- **Repository name:** `nac`
- **Description:** `Network Access Control para MikroTik RouterOS`
- **Visibility:** Public (para poder usar Railway)
- ✅ **Add .gitignore:** Already have one
- ✅ **Add README:** Already have one
- **License:** MIT (opcional)

### 1.3 Click en "Create repository"

---

## Paso 2: Conectar Repositorio Local a GitHub

### 2.1 Copiar URL del repositorio
```
Cuando creates el repo, GitHub te dará una URL como:
https://github.com/adrpinto83/nac.git
```

### 2.2 Agregar el remote
```bash
cd /home/adrpinto/miktotik
git remote add origin https://github.com/adrpinto83/nac.git
```

### 2.3 Renombrar rama (opcional pero recomendado)
```bash
git branch -M main
```

### 2.4 Agregar archivos
```bash
git add -A
```

### 2.5 Verificar qué se va a committir
```bash
git status
```

**Debe mostrar (no .env):**
```
app/
static/
tests/
requirements.txt
README.md
Dockerfile
Procfile
railway.json
.env.example
DEPLOYMENT.md
etc...
```

### 2.6 Crear commit inicial
```bash
git commit -m "Initial commit: MikroTik NAC System

- FastAPI application with JWT authentication
- Real-time device monitoring
- MikroTik router integration
- Load balancing and failover support
- Modern dashboard UI
- Ready for Railway deployment"
```

### 2.7 Subir a GitHub
```bash
git push -u origin main
```

---

## Paso 3: Desplegar en Railway

### 3.1 Opción A: Deploy Automático (Recomendado)

En GitHub, dentro del repositorio:
1. Click en "Add file" → "Create new file"
2. Nombre: `.railway.json`
3. Contenido:
```json
{
  "build": {
    "builder": "heroku.buildpacks"
  },
  "deploy": {
    "startCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health"
  }
}
```
4. Commit
5. Ir a [railway.app](https://railway.app)
6. Click "New Project" → "Deploy from GitHub"
7. Seleccionar tu repositorio
8. Configurar variables de entorno

### 3.2 Opción B: Deploy Manual

1. Ir a [railway.app](https://railway.app)
2. Click "New Project"
3. Click "Deploy from GitHub Repo"
4. Autorizar Railway con GitHub
5. Seleccionar repositorio `nac`
6. Railway detecta automáticamente el Procfile
7. Deploy inicia automáticamente

---

## Paso 4: Configurar Variables de Entorno en Railway

En Railway Dashboard:

### 4.1 Ir a Variables
```
Project → Variables
```

### 4.2 Agregar variables (copiar de .env.example)
```
ROUTER_IP=192.168.88.1
ROUTER_PORT=8728
ROUTER_USER=admin
ROUTER_PASSWORD=

SECRET_KEY=[generar-con-openssl]
DEBUG=False
LOG_LEVEL=INFO

CORS_ORIGINS=https://<tu-app>.railway.app,http://localhost:8080
```

### 4.3 Generar SECRET_KEY
```bash
openssl rand -hex 32
```

---

## Paso 5: Verificar Deployment

### 5.1 En Railway Dashboard
- Status debe ser "Running" (verde)
- Ver logs en tiempo real
- URL de la app aparece arriba (https://<tu-app>.railway.app)

### 5.2 Probar la aplicación
```
https://<tu-app>.railway.app
```

### 5.3 Verificar endpoints
```bash
curl https://<tu-app>.railway.app/health
```

---

## Paso 6: Configurar Dominio Personalizado (Opcional)

En Railway:
1. Settings → Domains
2. Click "Add Custom Domain"
3. Ingresar tu dominio
4. Configurar DNS según instrucciones

---

## Troubleshooting

### Deployment falló
```
Revisar logs:
Railway → Deployments → Ver logs del build
```

### Error: Port binding failed
```
Railway asigna puerto automáticamente en $PORT
Procfile ya está configurado correctamente
```

### Error: Module not found
```
Instalar dependencias:
pip install -r requirements.txt
```

### Error: Router unreachable
```
Si el router está en tu red local:
- Railway está en cloud, no puede acceder a 192.168.88.1
- Usar ngrok para tunelizar: https://ngrok.com
- O desplegar en servidor local
```

---

## Comandos Rápidos

```bash
# Clonar después (en otra máquina)
git clone https://github.com/adrpinto83/nac.git
cd nac

# Setup local
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run local
python -m uvicorn app.main:app --reload

# Ver estado GitHub
git status
git log --oneline
```

---

## Confirmación

Cuando veas esto, ¡está todo listo!

```
✅ Código en GitHub
✅ Aplicación en Railway
✅ Variables configuradas
✅ Health check funcionando
✅ API documentada en /docs
```

---

**¡Deployment completado!** 🚀
