# 🚀 Guía de Deployment

## Railway Deployment

### 1. Requisitos Previos
- Cuenta en [railway.app](https://railway.app)
- GitHub conectado

### 2. Pasos de Deployment

#### Opción A: Automático (Recomendado)
```
Click en: Deploy on Railway
```

#### Opción B: Manual
```bash
1. Ir a https://railway.app
2. New Project → GitHub Repo
3. Seleccionar nac
4. Railway detecta automáticamente Procfile
5. Deployment inicia automáticamente
```

### 3. Configurar Variables de Entorno

En Railway Dashboard → Variables:

```
ROUTER_IP=192.168.88.1
ROUTER_PORT=8728
ROUTER_USER=admin
ROUTER_PASSWORD=

SECRET_KEY=<generar-con-openssl>
DEBUG=False
LOG_LEVEL=INFO
```

Para generar SECRET_KEY:
```bash
openssl rand -hex 32
```

### 4. Database

Railway creará automáticamente:
- Volumen de datos persistente
- Base de datos SQLite

### 5. Verificar Deployment

```bash
# Ver logs
railway logs

# Ver status
railway status

# Acceder a la app
https://<tu-app>.railway.app
```

### 6. Troubleshooting

**Error: Port binding failed**
```
Railway asigna puerto automáticamente en variable $PORT
Procfile ya está configurado correctamente
```

**Error: Database locked**
```
Reiniciar la aplicación
Railway recrará la BD automáticamente
```

**Error: Router unreachable**
```
- Verificar ROUTER_IP está correcta
- Verificar router es accesible desde Railway
- Si es local, usar ngrok para tunelizar
```

## Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python -m uvicorn app.main:app --reload

# Access
http://localhost:8080
```

## Docker Local

```bash
# Build
docker build -t nac:latest .

# Run
docker run -p 8080:8080 -e ROUTER_IP=192.168.88.1 nac:latest

# Access
http://localhost:8080
```

## Production Checklist

- [ ] SECRET_KEY configurada aleatoriamente
- [ ] DEBUG=False
- [ ] ROUTER_IP, ROUTER_USER, ROUTER_PASSWORD correctos
- [ ] CORS_ORIGINS actualizado
- [ ] Logs configurados
- [ ] Database persistente
- [ ] Backups automáticos

---

¡Deployment completado! 🎉
