# 🔌 Instrucciones de Conexión Física - MikroTik NAC System

## Estado Actual de Configuración

Router configurado con los siguientes puertos:
- **Puerto 1**: WAN (Para ISP)
- **Puerto 2**: LAN (Disponible)
- **Puerto 3**: LAN (Para AP)
- **Puerto 4**: LAN (Disponible)
- **Puerto 5**: LAN (Administración)

---

## ✅ Esquema de Conexión

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│                    INTERNET (ISP)                           │
│                         │                                   │
│                         ↓                                   │
│                    ╔═══════════╗                            │
│                    ║ PUERTO 1  ║  ← Conecta ISP aquí       │
│                    ║   (WAN)   ║                            │
│    ╔═══════════════╩═══════════╩═══════════════╗            │
│    ║         MikroTik Router                  ║            │
│    ║                                           ║            │
│    ║ PUERTO 2  PUERTO 3  PUERTO 4  PUERTO 5  ║            │
│    ║  (LAN)    (LAN-AP)  (LAN)    (LAN-ADM)  ║            │
│    ╚═════╤═══════╤═══════╤═════════╤═════════╝            │
│          │       │       │         │                        │
│          │       │       │    [Tu PC Admin]                │
│          │       │       │      (192.168.88.x)             │
│          │       │       │                                   │
│          │       │    [Dispositivos                         │
│          │       │     LAN]                                 │
│          │       │     (192.168.88.x)                      │
│          │       │                                           │
│          │    [Access Points]                               │
│          │    (192.168.88.x)                               │
│          │    🔁 Distribuye WiFi                           │
│          │       │                                           │
│    [Otros LAN]   └─→ [Usuarios WiFi D1405]                │
│                         ├─ Splash Page (/splash)           │
│                         ├─ Registro automático              │
│                         ├─ Aprobación admin                │
│                         └─ Internet (via ISP)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Paso a Paso de Conexión Física

### Paso 1: Desconectar Config Actual
```
⚠️ Actualmente el puerto 5 está conectado a tu PC
1. Desconecta tu PC del puerto 5 (temporalmente)
2. Guarda la IP del router: 192.168.88.1
```

### Paso 2: Conectar ISP en Puerto 1
```
1. Toma el cable del ISP
2. Conéctalo en PUERTO 1 del router
3. Espera 5-10 segundos para que obtenga IP
4. El router obtendrá IP automáticamente via DHCP
```

### Paso 3: Conectar Access Point en Puerto 3
```
1. Toma el cable del Access Point
2. Conéctalo en PUERTO 3 del router
3. El AP recibirá IP: 192.168.88.x via DHCP
4. El AP comenzará a distribuir WiFi
```

### Paso 4: Reconectar PC Administrativo en Puerto 5
```
1. Conecta tu PC en PUERTO 5
2. Tu PC recibirá IP: 192.168.88.x via DHCP
3. Puedes acceder al dashboard:
   - URL: http://192.168.88.1:8080
   - O: http://192.168.88.5:8080 (si NAC está aquí)
```

---

## 🔍 Verificación de Conexiones

### Después de conectar ISP (Puerto 1)
```
✓ El router debe obtener IP del ISP
✓ Verifica: /ip address print
✓ Deberías ver IP tipo 192.168.1.x o similar (del ISP)
```

### Después de conectar AP (Puerto 3)
```
✓ El AP debe obtener IP 192.168.88.x
✓ El AP debe comenzar a distribuir WiFi
✓ Deberías ver SSID "WiFiD1405" disponible
```

### Después de reconectar PC (Puerto 5)
```
✓ Tu PC obtiene IP 192.168.88.x
✓ Puedes hacer ping al router: ping 192.168.88.1
✓ Puedes acceder al dashboard
```

---

## 🚀 Verificación del Sistema Completo

Una vez conectado todo:

### 1. Verificar Conectividad ISP
```bash
# Desde tu PC
ping 8.8.8.8
# Deberías obtener respuesta (internet funciona)
```

### 2. Verificar WiFi
```
1. Busca redes WiFi disponibles
2. Deberías ver "WiFiD1405" en la lista
3. Conectate (sin contraseña)
4. Deberías ser redirigido a splash page
```

### 3. Verificar Admin Dashboard
```
1. Abre: http://192.168.88.1:8080
2. Login: admin / admin123
3. Deberías ver dashboard con estadísticas
```

### 4. Verificar Pending Users
```
1. En dashboard, ve a "Pending Users"
2. Intenta registrarte desde WiFi
3. Deberías ver el usuario pendiente
4. Aprueba y verifica internet
```

---

## 📊 Estado de Puertos (Tabla Rápida)

| Puerto | Nombre | Tipo | Conexión | Red | Estado |
|--------|--------|------|----------|-----|--------|
| 1 | ether1 | WAN | ISP | 192.168.1.x* | ✅ Activo |
| 2 | ether2 | LAN | Disponible | 192.168.88.0/24 | ✅ Activo |
| 3 | ether3 | LAN | Access Point | 192.168.88.0/24 | ✅ Activo |
| 4 | ether4 | LAN | Disponible | 192.168.88.0/24 | ✅ Activo |
| 5 | ether5 | LAN | Admin PC | 192.168.88.0/24 | ✅ Activo |
| WiFi | wlan1 | WIFI | WiFiD1405 | 192.168.88.0/24 | ✅ Activo |

*IP obtenida del ISP via DHCP

---

## ⚠️ Notas Importantes

### Sobre ISP (Puerto 1)
- Obtiene IP automáticamente del ISP
- NO tiene IP fija 192.168.88.x
- Router actúa como "puente" entre ISP y LAN interna
- Todo el tráfico de internet pasa por aquí

### Sobre LAN (Puertos 2-5, WiFi)
- Red interna fija: 192.168.88.0/24
- DHCP activo: 192.168.88.100-200
- Todos los dispositivos en esta red pueden verse
- Pero internet solo si están en "authenticated-users"

### Sobre Access Point (Puerto 3)
- Obtiene IP: 192.168.88.x via DHCP
- Distribuye WiFi: WiFiD1405
- Los usuarios se conectan a este WiFi
- Son redirigidos a splash page para registro

---

## 🔧 Troubleshooting

### No tengo internet en WiFi después de conectar ISP
```
1. Verifica que puerto 1 obtuvo IP: /ip address print
2. Verifica firewall: /ip firewall filter print
3. Verifica que usuario está en "authenticated-users"
4. Revisa NAT rules: /ip firewall nat print
```

### No veo WiFiD1405
```
1. Verifica wireless: /interface wireless print
2. Verifica que está en AP bridge mode
3. Intenta reiniciar: /interface wireless reset
4. Cambia canal: /interface wireless set channel=6
```

### No puedo acceder a admin dashboard
```
1. Verifica IP: ipconfig (Windows) o ifconfig (Mac/Linux)
2. Intenta: http://192.168.88.1:8080
3. También: http://192.168.88.5:8080
4. Limpia cache del navegador
```

---

## ✅ Checklist Final

- [ ] ISP conectado en Puerto 1
- [ ] Router obtuvo IP del ISP
- [ ] Access Point conectado en Puerto 3
- [ ] AP obtiene IP 192.168.88.x
- [ ] WiFiD1405 visible en redes disponibles
- [ ] PC Admin conectado en Puerto 5
- [ ] PC Admin tiene acceso a dashboard
- [ ] Puedo conectarme a WiFiD1405
- [ ] Veo splash page al abrir navegador
- [ ] Puedo registrarme en splash page
- [ ] Admin puede aprobar usuarios
- [ ] Usuario aprobado tiene internet

---

**¡Sistema Listo para Usar!** 🎉

Contacto: Ver DEPLOYMENT_STATUS.md para soporte
