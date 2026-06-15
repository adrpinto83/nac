#!/bin/bash

# ============================================================================
# Script para configurar automáticamente el router MikroTik
# Dual ISP + APs + Balanceo de Carga
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🚀 MikroTik Dual ISP + APs Configuration Script             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que .env existe
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: archivo .env no encontrado${NC}"
    echo "Por favor, crear .env con:"
    echo "  cp .env.example .env"
    echo "  # Editar con credenciales del router"
    exit 1
fi

# Cargar variables de .env
export $(cat .env | grep -v '^#' | xargs)

if [ -z "$ROUTER_IP" ]; then
    echo -e "${RED}❌ ROUTER_IP no definida en .env${NC}"
    exit 1
fi

if [ -z "$ROUTER_PASSWORD" ]; then
    echo -e "${RED}❌ ROUTER_PASSWORD no definida en .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuración cargada${NC}"
echo "   Router IP: $ROUTER_IP"
echo "   Usuario: $ROUTER_USER"
echo ""

# Verificar que el script existe
if [ ! -f routeros/router_setup_dual_isp.rsc ]; then
    echo -e "${RED}❌ Script no encontrado: routeros/router_setup_dual_isp.rsc${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  ADVERTENCIA:${NC}"
echo "Esta operación:"
echo "  1. Hará un BACKUP de la configuración actual"
echo "  2. LIMPIARÁ la configuración existente"
echo "  3. Aplicará la nueva configuración Dual ISP"
echo ""
read -p "¿Deseas continuar? (s/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Cancelado."
    exit 1
fi

echo ""
echo -e "${YELLOW}⏳ Instalando dependencia: paramiko${NC}"
pip install paramiko -q

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error instalando paramiko${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Paramiko instalado${NC}"
echo ""

echo -e "${YELLOW}🚀 Iniciando configuración automática...${NC}"
echo ""

# Ejecutar script Python
python3 app/configure_router_dual_isp.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║   ✅ CONFIGURACIÓN APLICADA EXITOSAMENTE                       ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "📊 Estado actual:"
    echo "  - Backup guardado: backup_before_nac.rsc"
    echo "  - Interfaces: ether1-isp1, ether2-isp2, ether3-5 (APs), ether6-7 (LAN)"
    echo "  - Bridges: bridge-isp1, bridge-isp2, bridge-aps, bridge-lan"
    echo "  - DHCP: esperando IPs de ISPs..."
    echo ""
    echo "📝 Próximos pasos:"
    echo "  1. Ver docs/DUAL_ISP_LOADBALANCE.md para configurar balanceo"
    echo "  2. Conectar APs a puertos 3-5"
    echo "  3. Conectar dispositivos a puertos 6-7"
    echo "  4. Iniciar Sistema NAC: python -m uvicorn app.main:app"
    echo ""
else
    echo -e "${RED}❌ Error en la configuración${NC}"
    echo "Ver logs arriba para más detalles."
    exit 1
fi
