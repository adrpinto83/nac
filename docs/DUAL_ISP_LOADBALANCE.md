# 🌐 Configuración Dual ISP con Balanceo de Carga

Guía para configurar MikroTik hAP ac3 con dos proveedores de internet (ISP) y balanceo de carga.

## 📋 Topología de Red

```
┌─────────────────────────────────────────────────────────────────┐
│                         MikroTik hAP ac3                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PUERTOS WAN (Internet):                                        │
│  ├─ Puerto 1 (ether1-isp1) ──→ ISP 1 (Modem 1)                │
│  └─ Puerto 2 (ether2-isp2) ──→ ISP 2 (Modem 2)                │
│                                                                 │
│  PUERTOS ACCESO (APs):                                          │
│  ├─ Puerto 3 (ether3-ap) ──→ Access Point 1 (VLAN 100)        │
│  ├─ Puerto 4 (ether4-ap) ──→ Access Point 2 (VLAN 100)        │
│  └─ Puerto 5 (ether5-ap) ──→ Access Point 3 (VLAN 100)        │
│                                                                 │
│  PUERTOS LAN (Local):                                           │
│  ├─ Puerto 6 (ether6-lan) ──→ Switches/Devices (VLAN 200)     │
│  └─ Puerto 7 (ether7-gerencia) ──→ PC Gerencia (VLAN 200)     │
│                                                                 │
│  WIFI:                                                          │
│  ├─ WiFi 5GHz ──→ Red de APs (conectado a puertos 3-5)       │
│  └─ WiFi 2.4GHz ──→ Red de Guests (opcional)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuración Paso a Paso

### Paso 1: Aplicar Script de Configuración

```bash
# Copiar el script al router
scp routeros/router_setup_dual_isp.rsc admin@192.168.88.1:/

# Conectarse al router
ssh admin@192.168.88.1

# Ejecutar el script
/import router_setup_dual_isp.rsc
```

### Paso 2: Verificar Configuración

```bash
# Conectarse al router
ssh admin@192.168.88.1

# Verificar interfaces
/interface print

# Verificar bridges
/interface bridge print
/interface bridge port print

# Verificar direcciones IP
/ip address print
```

**Esperado:**
```
ether1-isp1    - DHCP (esperando IP de ISP 1)
ether2-isp2    - DHCP (esperando IP de ISP 2)
ether3-ap      - bridge-aps
ether4-ap      - bridge-aps
ether5-ap      - bridge-aps
ether6-lan     - bridge-lan (192.168.88.1)
ether7-gerencia - bridge-lan (192.168.88.1)
```

### Paso 3: Esperar a que DHCP Asigne IPs

```bash
# Esperar 30-60 segundos a que los módems asignen IPs

# Verificar IPs asignadas
/ip address print

# Deberías ver:
# - dhcp-isp1 con IP de ISP 1
# - dhcp-isp2 con IP de ISP 2
```

### Paso 4: Configurar Balanceo de Carga (PCC)

Una vez que ISP1 e ISP2 tienen IPs, configurar balanceo:

```bash
# Obtener las IPs asignadas por DHCP
/ip dhcp-client print

# Anotar las IPs gateway de cada ISP
# ISP1 Gateway: <IP_ISP1_GATEWAY>
# ISP2 Gateway: <IP_ISP2_GATEWAY>
```

Luego ejecutar (reemplazar las IPs):

```bash
# Agregar reglas de Mangle para PCC (Per Connection Classifier)
/ip firewall mangle add chain=prerouting dst-address-type=!local \
    new-routing-mark=isp1 passthrough=yes \
    per-connection-classifier=both-addresses-and-ports:2/0 \
    comment="PCC to ISP1"

/ip firewall mangle add chain=prerouting dst-address-type=!local \
    new-routing-mark=isp2 passthrough=yes \
    per-connection-classifier=both-addresses-and-ports:2/1 \
    comment="PCC to ISP2"

# Eliminar rutas default anteriores
/ip route remove [find dst-address=0.0.0.0/0]

# Agregar rutas con routing marks
/ip route add dst-address=0.0.0.0/0 \
    gateway=<IP_ISP1_GATEWAY> routing-mark=isp1 \
    comment="Route via ISP1" distance=10

/ip route add dst-address=0.0.0.0/0 \
    gateway=<IP_ISP2_GATEWAY> routing-mark=isp2 \
    comment="Route via ISP2" distance=10

# Ruta default como fallback
/ip route add dst-address=0.0.0.0/0 \
    gateway=<IP_ISP1_GATEWAY> comment="Default Route" distance=20
```

## 📊 Redes Configuradas

| Red | VLAN | Rango | Gateway | Uso |
|-----|------|-------|---------|-----|
| APs | 100 | 192.168.100.0/24 | 192.168.100.1 | Access Points |
| LAN | 200 | 192.168.88.0/24 | 192.168.88.1 | Gerencia + Devices |
| ISP1 | - | DHCP | DHCP | WAN Primary |
| ISP2 | - | DHCP | DHCP | WAN Secondary |

## ⚖️ Balanceo de Carga (PCC)

### Cómo Funciona

**PCC (Per Connection Classifier)** divide las conexiones entre los ISPs:

1. Cada conexión se clasifica basándose en:
   - Dirección IP origen
   - Dirección IP destino
   - Puerto origen
   - Puerto destino

2. El clasificador `2/0` y `2/1` significa:
   - `2` = número de buckets (2 ISPs)
   - `/0` = primera mitad de conexiones → ISP1
   - `/1` = segunda mitad → ISP2

3. Las conexiones se distribuyen de forma más o menos equitativa

### Ventajas

✅ Balanceo automático de carga  
✅ Failover si un ISP cae  
✅ Mayor ancho de banda total  
✅ Mejor uso de recursos  

### Desventajas

⚠️ Algunas conexiones pueden ir al ISP lento  
⚠️ No es perfectamente equitativo  
⚠️ Requiere dos proveedores diferentes  

## 🎛️ Alternativa: Balanceo con Pesos

Si quieres dar más peso a un ISP:

```bash
# Ruta ISP1 con peso 10
/ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP1> distance=10

# Ruta ISP2 con peso 20 (menos prioridad)
/ip route add dst-address=0.0.0.0/0 gateway=<IP_ISP2> distance=20
```

ISP1 recibe más tráfico, ISP2 es fallback.

## 🔍 Monitoreo

### Ver Conexiones por ISP

```bash
# Ver tráfico en tiempo real
/interface monitor-traffic ether1-isp1
/interface monitor-traffic ether2-isp2

# Ver estadísticas de Mangle
/ip firewall mangle print stats
```

### Probar Failover

```bash
# 1. Desconectar Puerto 1 (ISP1)
# 2. Las conexiones automáticamente cambiarán a ISP2
# 3. Reconectar Puerto 1
# 4. Las nuevas conexiones balancearán de nuevo
```

## 🚀 Integración con NAC System

El sistema NAC puede monitorear:

1. **Salud de ISPs**
   ```bash
   # En scheduler tasks
   Health check a gateway de ISP1
   Health check a gateway de ISP2
   ```

2. **Tráfico por ISP**
   ```bash
   # Via REST API
   /interface/ether1-isp1/monitor
   /interface/ether2-isp2/monitor
   ```

3. **Alertas si un ISP cae**
   ```
   - Verificar accesibilidad del gateway
   - Si falla, generar alerta
   - Registrar en audit_log
   ```

## 🆘 Troubleshooting

### "Solo funciona un ISP"

**Verificar:**
```bash
# 1. ¿Ambos modems están conectados?
ping <gateway_isp1>
ping <gateway_isp2>

# 2. ¿Las rutas están creadas?
/ip route print

# 3. ¿Los mangle rules están activos?
/ip firewall mangle print
```

### "El balanceo no funciona equitativamente"

**Nota:** PCC no distribuye exactamente 50/50. Depende del patrón de conexiones.

**Solución:**
```bash
# Si necesitas distribución exacta, usar balanceo por interfaz:
# (más complejo, requiere script personalizado)
```

### "Latencia inconsistente"

**Causas:**
- Velocidades diferentes entre ISPs
- Saturación en uno de los ISPs
- Problemas con modems

**Solución:**
```bash
# Monitorear latencia de cada ISP
# Usar pesos de distancia para favorecer el más rápido
/ip route add dst-address=0.0.0.0/0 gateway=<FAST_ISP> distance=10
/ip route add dst-address=0.0.0.0/0 gateway=<SLOW_ISP> distance=20
```

## 📈 Optimizaciones Adicionales

### 1. QoS por ISP

```bash
# Limitar ancho de banda por ISP
/queue simple add name=isp1-limit target=ether1-isp1 max-limit=10M/10M
/queue simple add name=isp2-limit target=ether2-isp2 max-limit=10M/10M
```

### 2. Prioridad de Tráfico

```bash
# Priorizar tráfico VoIP
/ip firewall mangle add chain=forward protocol=udp dst-port=5060 \
    new-priority=1 passthrough=yes comment="VoIP Priority"
```

### 3. Cache DNS Local

```bash
# Ya configurado: caché de 2048 registros
/ip dns print

# Para más capacidad:
/ip dns set cache-size=8192
```

## 📝 Checklist de Verificación

- [ ] Ambos ISPs conectados a puertos 1 y 2
- [ ] APs conectadas a puertos 3-5
- [ ] DHCP asignó IPs a ambos ISPs
- [ ] Rutas configuradas con gateways correctos
- [ ] Mangle rules configuradas (PCC)
- [ ] Ping a ambos gateways funciona
- [ ] REST API habilitada en puerto 80
- [ ] Usuario `api-container` creado
- [ ] Sistema NAC puede conectarse al router
- [ ] Dashboard muestra ambos ISPs saludables

## 🔗 Recursos Relacionados

- [INSTALACION.md](../INSTALACION.md) - Instalación del sistema NAC
- [ARQUITECTURA.md](ARQUITECTURA.md) - Arquitectura del sistema
- [SCHEDULER.md](SCHEDULER.md) - Monitoreo automático
- [ROUTEROS_CLIENT.md](ROUTEROS_CLIENT.md) - API del cliente RouterOS

## 🎓 Referencias MikroTik

- **PCC Balancing**: Oficial MikroTik docs
- **Dual WAN**: mikrotik.com/tutorials
- **Firewall NAT**: wiki.mikrotik.com/wiki/Manual:IP/Firewall/NAT

---

**Nota:** Esta configuración está lista para integrarse con el sistema NAC completo. El scheduler puede monitorear la salud de ambos ISPs y generar alertas si alguno falla.
