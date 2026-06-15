# 🔧 Guía Manual - Configuración del MikroTik

**Si los scripts automáticos no funcionan, sigue estos pasos manualmente.**

---

## 📍 OPCIÓN 1: Configurar via WebFig (Recomendado - Más fácil)

### Paso 1: Acceder a WebFig
```
1. Abre navegador: http://192.168.88.1
2. Usuario: admin
3. Contraseña: NAC_MikroTik_2025
```

### Paso 2: Renombrar Interfaces
```
Interfaces → Ethernet
1. ether1 → Renombrar a: ether1-isp1
2. ether2 → Renombrar a: ether2-isp2
3. ether5 → Renombrar a: ether5-admin
```

### Paso 3: Configurar DHCP Clients (ISPs)
```
IP → DHCP Client
1. Click [+] New
   - Interface: ether1-isp1
   - Disabled: NO
   - Click [Apply] [OK]

2. Click [+] New
   - Interface: ether2-isp2
   - Disabled: NO
   - Click [Apply] [OK]
```

### Paso 4: Configurar IP Admin
```
IP → Addresses
1. Click [+] New
   - Address: 192.168.88.5/24
   - Interface: ether5-admin
   - Click [Apply] [OK]
```

### Paso 5: Crear Bridge para APs
```
Interfaces → Bridges
1. Click [+] New
   - Name: bridge-aps
   - Click [Apply] [OK]

2. Bridge Ports
   - Click [+] New
     - Bridge: bridge-aps
     - Interface: ether3
   - Click [Apply] [OK]

   - Click [+] New
     - Bridge: bridge-aps
     - Interface: ether4
   - Click [Apply] [OK]

   - Click [+] New
     - Bridge: bridge-aps
     - Interface: ether6
   - Click [Apply] [OK]
```

### Paso 6: Configurar IP del Bridge
```
IP → Addresses
1. Click [+] New
   - Address: 192.168.88.1/24
   - Interface: bridge-aps
   - Click [Apply] [OK]
```

### Paso 7: Configurar DHCP Server
```
IP → DHCP Server
1. DHCP Servers → Click [+] New
   - Name: dhcp-aps
   - Interface: bridge-aps
   - Disabled: NO
   - Click [Apply] [OK]

2. DHCP Networks → Click [+] New
   - Address: 192.168.88.0/24
   - Gateway: 192.168.88.1
   - DNS Servers: 8.8.8.8,8.8.4.4
   - Click [Apply] [OK]
```

### Paso 8: Configurar NAT
```
IP → Firewall → NAT
1. Click [+] New
   - Chain: srcnat
   - Out. Interface: ether1-isp1
   - Action: masquerade
   - Click [Apply] [OK]

2. Click [+] New
   - Chain: srcnat
   - Out. Interface: ether2-isp2
   - Action: masquerade
   - Click [Apply] [OK]

3. Click [+] New
   - Chain: srcnat
   - Out. Interface: ether5-admin
   - Action: masquerade
   - Click [Apply] [OK]
```

### Paso 9: Configurar Firewall
```
IP → Firewall → Filter Rules
1. Click [+] New
   - Chain: forward
   - Action: accept
   - Connection State: established,related
   - Click [Apply] [OK]

2. Click [+] New
   - Chain: forward
   - Action: drop
   - Connection State: invalid
   - Click [Apply] [OK]
```

### Paso 10: Configurar DNS
```
IP → DNS
- Servers: 8.8.8.8 8.8.4.4
- Click [Apply]
```

### Paso 11: Guardar Configuración
```
File → Save Configuration
```

---

## 📍 OPCIÓN 2: Configurar via Console (Terminal)

### Conectar a la Console
```bash
# Si tienes acceso a la console física del router:
1. Conecta un cable serial (RJ45 a DB9)
2. Abre terminal serial (9600 baud, 8N1)
3. Presiona Enter
4. Login: admin / NAC_MikroTik_2025
```

### Ejecutar Comandos
```
# 1. Renombrar interfaces
/interface ethernet set ether1 name=ether1-isp1
/interface ethernet set ether2 name=ether2-isp2
/interface ethernet set ether5 name=ether5-admin

# 2. DHCP Clients (ISPs)
/ip dhcp-client add interface=ether1-isp1 disabled=no
/ip dhcp-client add interface=ether2-isp2 disabled=no

# 3. IP Admin
/ip address add address=192.168.88.5/24 interface=ether5-admin

# 4. Bridge
/interface bridge add name=bridge-aps
/interface bridge port add bridge=bridge-aps interface=ether3
/interface bridge port add bridge=bridge-aps interface=ether4
/interface bridge port add bridge=bridge-aps interface=ether6
/ip address add address=192.168.88.1/24 interface=bridge-aps

# 5. DHCP Server
/ip dhcp-server add name=dhcp-aps interface=bridge-aps disabled=no
/ip dhcp-server network add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=8.8.8.8,8.8.4.4

# 6. NAT
/ip firewall nat add chain=srcnat out-interface=ether1-isp1 action=masquerade
/ip firewall nat add chain=srcnat out-interface=ether2-isp2 action=masquerade
/ip firewall nat add chain=srcnat out-interface=ether5-admin action=masquerade

# 7. Firewall
/ip firewall filter add chain=forward action=accept connection-state=established,related
/ip firewall filter add chain=forward action=drop connection-state=invalid

# 8. DNS
/ip dns set servers=8.8.8.8,8.8.4.4

# 9. Guardar
/system save
```

---

## ✅ Verificación después de Configurar

### Ver configuración aplicada

**via WebFig:**
```
1. Interfaces → Ethernet
   - Ver ether1-isp1, ether2-isp2, ether5-admin
   - Ver bridge-aps

2. IP → Addresses
   - Ver 192.168.88.5/24 en ether5-admin
   - Ver 192.168.88.1/24 en bridge-aps

3. IP → DHCP Server
   - Ver dhcp-aps activo en bridge-aps
   - Ver network 192.168.88.0/24

4. IP → DHCP Server → Leases
   - Ver dispositivos conectados con IPs 192.168.88.100-200
```

**via Terminal:**
```bash
# En el router (console o SSH si funciona):
/interface print
/ip address print
/ip dhcp-server lease print
/ip dhcp-client print
/ip firewall nat print
/system identity print
```

---

## 🔌 Conectar Dispositivos

### Paso 1: Conectar ISPs
```
1. Toma el cable Ethernet del Modem ISP1
2. Conecta al Puerto 1 del MikroTik (ether1-isp1)
3. Espera 30 segundos a que obtenga IP via DHCP
4. Verifica: IP → DHCP Client → Ver IP obtenida

Repite para ISP2 en Puerto 2 (ether2-isp2)
```

### Paso 2: Conectar PC Admin
```
1. Conecta una PC al Puerto 5 del MikroTik (ether5-admin)
2. La PC obtendrá IP automática en rango 192.168.88.x
3. Abre navegador: http://192.168.88.1
4. Debería ver WebFig del router
```

### Paso 3: Conectar Access Points
```
1. Conecta AP1 al Puerto 3
2. Conecta AP2 al Puerto 4
3. Conecta AP3 al Puerto 6

Los APs obtendrán IPs del DHCP:
- 192.168.88.100, 192.168.88.101, etc.

Configura cada AP para que:
- Obtenga IP via DHCP
- Conecte a los puertos ethernet del MikroTik
```

---

## 🧪 Probar Internet

### Desde PC Admin (Puerto 5)
```bash
# Verificar IP
ipconfig (Windows) o ifconfig (Linux)
# Debería mostrar: 192.168.88.x (entre 5-254)

# Probar conectividad
ping 8.8.8.8
# Debería responder

# Probar DNS
ping google.com
# Debería responder
```

### Desde Access Points
```
1. Conecta un dispositivo (teléfono, laptop) a los APs
2. Obtiene IP automática 192.168.88.100-200
3. Abre navegador: http://google.com
4. Debería cargar la página (Internet funciona)
```

---

## 🌐 Acceso a NAC System

### Dashboard
```
http://localhost:8080

Debería mostrar:
- Usuarios conectados (desde APs y puerto 5)
- IPs asignadas (192.168.88.x)
- Dispositivos en línea
- Ancho de banda consumido
```

### Ver Dispositivos en Tiempo Real
```
http://localhost:8080/api/devices/live

Mostrará tabla ARP con:
- MAC Address
- IP asignada
- Interfaz conectada
```

---

## 🐛 Troubleshooting

### ISP sin IP
```
Síntoma: ether1-isp1 o ether2-isp2 sin IP pública

Solución:
1. Verifica que Modem ISP esté encendido
2. Verifica cable Ethernet
3. En WebFig → IP → DHCP Client
4. Si existe pero sin IP:
   - Desactiva y reactiva
   - O elimina y crea de nuevo
```

### Admin PC sin conexión
```
Síntoma: PC en puerto 5 no obtiene IP

Solución:
1. Verifica que bridge-aps existe en WebFig
2. Verifica que DHCP Server dhcp-aps está activo
3. Si no:
   - Elimina y crea de nuevo
   - Verifica rango 192.168.88.100-200
```

### APs sin Internet
```
Síntoma: APs conectados pero sin acceso a Internet

Solución:
1. Verifica que ether1-isp1 y/o ether2-isp2 tienen IP
2. Verifica que NAT existe y está activo
3. Verifica firewall forward accept
4. Si un ISP falla, usa el otro
```

---

## 📊 Ver IPs en la Aplicación

### Dashboard
```
http://localhost:8080

1. Login con credenciales
2. Ir a "Dispositivos" o "Live Devices"
3. Ver tabla de dispositivos conectados
4. Ver IPs asignadas (192.168.88.x)
5. Ver consumo de ancho de banda
```

### Tabla ARP en Tiempo Real
```
curl http://localhost:8080/api/devices/live

Respuesta JSON:
[
  {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.100",
    "interface": "bridge-aps",
    "status": "online"
  }
]
```

---

## 🔐 Cambios Recomendados para Producción

### Cambiar contraseña admin
```
WebFig → System → Users → admin
- Password: [nueva contraseña segura]
- Click [Apply]
```

### Limitar acceso SSH (si lo activas)
```
Firewall → Filter Rules
- Agregar regla para rechazar SSH desde WAN
```

### Configurar HTTPS
```
System → Certificates
- Generar certificado
- Configurar en WebFig port 443
```

---

## ✅ Checklist Final

- [ ] ether1-isp1 renombrada y con DHCP cliente
- [ ] ether2-isp2 renombrada y con DHCP cliente
- [ ] ether5-admin renombrada con IP 192.168.88.5/24
- [ ] bridge-aps creado con puertos 3,4,6
- [ ] IP 192.168.88.1/24 en bridge-aps
- [ ] DHCP Server dhcp-aps activo en bridge-aps
- [ ] Network DHCP 192.168.88.0/24 configurada
- [ ] NAT masquerade para 3 interfaces
- [ ] Firewall forward rules activas
- [ ] DNS configurado (8.8.8.8, 8.8.4.4)
- [ ] Configuración guardada (/system save)
- [ ] ISP1 conectado a puerto 1 y con IP pública
- [ ] ISP2 conectado a puerto 2 y con IP pública
- [ ] PC Admin conectada a puerto 5 y con IP
- [ ] Access Points conectados y con DHCP
- [ ] Prueba de Internet: ping 8.8.8.8 ✅
- [ ] NAC System ve dispositivos conectados

---

¡Una vez completado, tu red estará lista! 🎉
