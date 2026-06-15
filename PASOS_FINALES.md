# 🚀 PASOS FINALES - EJECUTA ESTO EN TU WSL

## ⚠️ IMPORTANTE
**NO ejecutes nada desde internet. Todo debe ser desde tu WSL local donde estás conectado al router via Ethernet.**

---

## PASO 1: Instala dependencias

```bash
cd /home/adrpinto/miktotik
pip install -r requirements.txt
```

Espera a que termine.

---

## PASO 2: Verifica conexión al router

```bash
ping 192.168.88.1
```

Debe responder sin "General failure".

---

## PASO 3: Conecta via SSH

```bash
ssh admin@192.168.88.1
```

Deberías entrar sin errores. Escribe `exit` para salir.

---

## PASO 4: Configura el router

```bash
python3 app/configure_router_dual_isp.py
```

**IMPORTANTE**: Déjalo terminar completamente. No interrumpas.
Puede tardar 5-10 minutos.

Verás:
```
✅ Conectado al router
✅ Backup guardado
✅ Script subido
✅ Configuración aplicada
✅ ISP1 obtuvo IP
✅ ISP2 obtuvo IP (cuando conectes puerto 2)
```

---

## PASO 5: Verifica configuración

```bash
python3 app/verify_router_config.py
```

Deberías ver:
```
✅ ether1-isp1
✅ ether2-isp2
✅ ether3-ap
✅ bridge-aps
✅ dhcp-aps
✅ REST API
✅ api-container
```

---

## PASO 6: Configura balanceo de carga

```bash
python3 app/configure_load_balance.py
```

---

## PASO 7: Inicia Sistema NAC

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Cuando veas:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete
```

El Sistema NAC está listo.

---

## PASO 8: Accede al Dashboard

En tu navegador:
```
http://localhost:8080
```

---

## ✅ CHECKLIST

- [ ] Instalé dependencias
- [ ] Ping al router funciona
- [ ] SSH al router funciona
- [ ] Configure el router (paso 4)
- [ ] Verifiqué configuración (paso 5)
- [ ] Configure balanceo (paso 6)
- [ ] Inicié Sistema NAC (paso 7)
- [ ] Accedí a http://localhost:8080 (paso 8)

---

## 📝 NOTAS

- **NO interrumpas** los scripts mientras ejecutan
- **NO cierres** la ventana de PowerShell/CMD
- **Si hay error**: Lee el mensaje de error y dime exactamente qué dice
- **Si se cuelga**: Espera 5 minutos antes de parar
- **Tu PC debe estar conectada** via Ethernet al router

---

¿Ejecutas estos pasos ahora? 🚀
