# 🔧 Configuración Inicial del MikroTik para NAC System

**Fecha:** 15 de Junio de 2026  
**Estado:** ⏳ En Proceso

---

## 📋 Arquitectura de Red

```
INTERNET
  ├─ ISP1 (IP pública X.X.X.X)
  │   └─ Conectar al Puerto 1 (ether1-isp1) [DHCP]
  │
  └─ ISP2 (IP pública Y.Y.Y.Y)
      └─ Conectar al Puerto 2 (ether2-isp2) [DHCP]

MikroTik Router (192.168.88.1)
  ├─ ether1-isp1 → ISP1 (DHCP WAN)
  ├─ ether2-isp2 → ISP2 (DHCP WAN)
  ├─ ether5-admin → Administración local (192.168.88.5/24)
  │   └─ Acceso directo con Internet
  │
  └─ bridge-aps → Access Points (DHCP 192.168.88.100-200)
      ├─ ether3 → AP 1
      ├─ ether4 → AP 2
      └─ ether6 → AP 3

CLIENTES
  ├─ Desde ether5-admin → 192.168.88.5-254 (Admin + Internet)
  └─ Desde AP (ether3,4,6) → 192.168.88.100-200 (Usuarios + Internet)
```

---

## 🔧 Configuración Aplicada

### 1. **Interfaces de Red**

| Interfaz | Propósito | Configuración | IP |
|----------|----------|---------------|----|
| ether1-isp1 | ISP 1 | DHCP WAN | Dinámica |
| ether2-isp2 | ISP 2 | DHCP WAN | Dinámica |
| ether5-admin | Admin Local | Estática | 192.168.88.5/24 |
| bridge-aps | Access Points | Bridge | 192.168.88.1/24 |

### 2. **DHCP Server**

- **Red:** 192.168.88.0/24
- **Pool:** 192.168.88.100-200
- **Gateway:** 192.168.88.1
- **DNS:** 8.8.8.8, 8.8.4.4
- **Interface:** bridge-aps (APs)

### 3. **NAT (Network Address Translation)**

```
ISP1  ← Masquerade desde ether1-isp1
ISP2  ← Masquerade desde ether2-isp2
Admin ← Masquerade desde ether5-admin
```

Esto permite que cualquier dispositivo conectado tenga acceso a Internet via cualquiera de los ISPs.

### 4. **Firewall**

- ✅ Forward: Permitir conexiones establecidas
- ✅ Forward: Permitir conexiones relacionadas
- ✅ Forward: Rechazar conexiones inválidas

---

## 📍 Conexiones Físicas

### Puerto 1 (ether1-isp1) - ISP 1
```
Modem ISP1 → Cabo Ethernet → Puerto 1 del MikroTik
↓
Recibe IP pública via DHCP
↓
Acceso a Internet
```

### Puerto 2 (ether2-isp2) - ISP 2
```
Modem ISP2 → Cabo Ethernet → Puerto 2 del MikroTik
↓
Recibe IP pública via DHCP
↓
Acceso a Internet (Redundancia/Load Balancing)
```

### Puerto 5 (ether5-admin) - Administración Local
```
PC Admin → Cabo Ethernet → Puerto 5 del MikroTik
↓
Asignación DHCP: 192.168.88.5-254
↓
Acceso local a 192.168.88.1 (WebFig)
↓
Acceso a Internet (NAT)
```

### Puertos 3, 4, 6 (bridge-aps) - Access Points
```
Access Point 1 → Puerto 3 del MikroTik
Access Point 2 → Puerto 4 del MikroTik
Access Point 3 → Puerto 6 del MikroTik
        ↓
    Bridge común
        ↓
  Asignación DHCP: 192.168.88.100-200
        ↓
    Acceso a Internet via ISP1/ISP2
```

---

## 🌐 Acceso a la Red

### Desde Puerto 5 (Admin)
```
IP Asignada: 192.168.88.5-254 (DHCP desde bridge-aps)
Puerta de Enlace: 192.168.88.1
DNS: 8.8.8.8, 8.8.4.4

Acceso:
  - Router: http://192.168.88.1/webfig
  - SSH: ssh admin@192.168.88.1
  - Internet: Automático (NAT activo)
```

### Desde Puertos 3,4,6 (Access Points)
```
IP Asignada: 192.168.88.100-200 (DHCP desde bridge-aps)
Puerta de Enlace: 192.168.88.1
DNS: 8.8.8.8, 8.8.4.4

Acceso:
  - Dispositivos WiFi: Conectarse a AP
  - IP: Obtener automáticamente via DHCP
  - Internet: Automático (NAT activo)
```

---

## 📊 Ver IPs en la Aplicación NAC

### Dashboard de la App
```
http://localhost:8080

Verás:
  📊 Estadísticas
  └─ Total de Usuarios: XX (desde IPs 192.168.88.x)
  └─ Usuarios Activos: XX (en tiempo real)
  └─ Dispositivos: XX (en tabla ARP del router)

  👥 Usuarios
  └─ Lista de direcciones MAC conectadas
  └─ IPs asignadas
  └─ Estado de conexión
  └─ Ancho de banda consumido
```

### Tabla ARP del Router
El router mantiene una tabla ARP con:
- Dirección MAC
- IP asignada (192.168.88.x)
- Nombre del dispositivo
- Tiempo de conexión

**Acceso:**
- WebFig: http://192.168.88.1 → IP → ARP
- API: `GET /api/devices/live` → Devuelve tabla ARP

---

## ✅ Verificación después de la Configuración

### 1. Verificar interfaces
```bash
ssh admin@192.168.88.1

# En el router:
/interface print
/ip address print

# Debería mostrar:
# ether1-isp1 con IP pública (via DHCP ISP1)
# ether2-isp2 con IP pública (via DHCP ISP2)
# ether5-admin con IP estática 192.168.88.5/24
# bridge-aps con IP 192.168.88.1/24
```

### 2. Verificar DHCP
```bash
# En el router:
/ip dhcp-server lease print

# Debería mostrar clientes conectados con IPs 192.168.88.100-200
```

### 3. Verificar NAT
```bash
# En el router:
/ip firewall nat print

# Debería mostrar 3 reglas masquerade (ISP1, ISP2, Admin)
```

### 4. Verificar conectividad
```bash
# Desde PC conectada a ether5-admin:
ping 8.8.8.8

# Debería responder (Internet funciona)
```

---

## 🚀 Próximos Pasos

### 1. Conectar ISPs
- [ ] Conectar Modem ISP1 al Puerto 1
- [ ] Conectar Modem ISP2 al Puerto 2
- [ ] Esperar a que obtengan IPs via DHCP

### 2. Conectar Admin
- [ ] Conectar PC Admin al Puerto 5
- [ ] Verificar que obtiene IP en rango 192.168.88.x
- [ ] Acceder a http://192.168.88.1

### 3. Conectar Access Points
- [ ] Conectar AP 1 al Puerto 3
- [ ] Conectar AP 2 al Puerto 4
- [ ] Conectar AP 3 al Puerto 6
- [ ] Verificar DHCP activo

### 4. Acceder a NAC System
- [ ] Abrir http://localhost:8080
- [ ] Ver dashboard
- [ ] Ver tabla de dispositivos conectados
- [ ] Ver IPs asignadas en tiempo real

---

## 🔍 Troubleshooting

### ISP sin Internet
```
Síntoma: ether1 o ether2 sin IP pública

Solución:
1. Verificar que modem ISP esté conectado y encendido
2. Verificar cable Ethernet
3. En router: /ip dhcp-client print
4. Si no funciona, deshabilitar y rehabilitar DHCP
```

### Admin sin DHCP
```
Síntoma: ether5 conectado pero sin IP

Solución:
1. Verificar que bridge-aps tiene DHCP activo
2. Verificar pool DHCP: /ip dhcp-server lease print
3. Si no funciona, reiniciar DHCP: /ip dhcp-server disable; /ip dhcp-server enable
```

### APs sin Internet
```
Síntoma: APs conectados pero sin acceso a Internet

Solución:
1. Verificar que bridge-aps está activo
2. Verificar reglas NAT: /ip firewall nat print
3. Verificar ISPs: /interface print
4. Si ISPs fallan, usar solo uno que funcione
```

---

## 📈 Monitoreo

### API Endpoints para Monitoreo

```bash
# Ver dispositivos conectados
curl http://localhost:8080/api/devices/live

# Ver estadísticas
curl http://localhost:8080/api/dashboard/metrics

# Ver usuarios
curl http://localhost:8080/api/users/

# Ver tabla ARP en vivo
curl http://localhost:8080/api/devices/live
```

---

## 🔐 Seguridad

⚠️ Configuración actual es **ABIERTA**. Para producción:

1. **Cambiar credenciales admin**
   ```
   /user set admin password=nuevacontraseña
   ```

2. **Habilitar firewall estricto**
   ```
   /ip firewall filter add chain=forward action=drop
   ```

3. **Limitar acceso SSH**
   ```
   /ip firewall filter add chain=input src-address=192.168.88.0/24 protocol=tcp dst-port=22 action=accept
   /ip firewall filter add chain=input protocol=tcp dst-port=22 action=drop
   ```

4. **Configurar certificado HTTPS**
   - Generar certificado auto-firmado
   - Configurar en WebFig

---

**¡Configuración lista!** 🎉

Conecta los ISPs y Access Points, luego verifica en el dashboard de NAC System.
