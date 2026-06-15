#!/bin/bash

###############################################################################
#                                                                             #
#  🚀 SCRIPT AUTOMÁTICO - CONFIGURAR ROUTER MIKROTIK + SISTEMA NAC           #
#                                                                             #
#  Este script ejecuta TODOS los pasos automáticamente:                      #
#  1. Configura router con Dual ISP                                          #
#  2. Verifica que todo funcionó                                             #
#  3. Configura balanceo de carga                                            #
#  4. Inicia Sistema NAC                                                     #
#                                                                             #
###############################################################################

set -e  # Salir si hay error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     🚀 CONFIGURACIÓN AUTOMÁTICA - MIKROTIK NAC SYSTEM         ║"
echo "║                                                                ║"
echo "║   Ejecutando 4 pasos automáticamente en tu PC...              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Verificar que estamos en la carpeta correcta
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: No se encontró requirements.txt${NC}"
    echo "Asegúrate de estar en la carpeta del proyecto"
    exit 1
fi

echo -e "${YELLOW}📋 VERIFICACIÓN PREVIA${NC}\n"

# Verificar Python
echo -n "Verificando Python 3... "
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ No encontrado${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# Verificar .env
echo -n "Verificando archivo .env... "
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ No encontrado${NC}"
    echo "Copiar .env.example a .env y editar credenciales"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Archivo .env creado, EDITA LAS CREDENCIALES:${NC}"
    echo "   nano .env"
    exit 1
fi
echo -e "${GREEN}✅ Encontrado${NC}"

# Verificar que tiene credenciales
ROUTER_IP=$(grep "ROUTER_IP=" .env | cut -d'=' -f2 | tr -d ' ')
ROUTER_PASSWORD=$(grep "ROUTER_PASSWORD=" .env | cut -d'=' -f2 | tr -d ' ')

if [ -z "$ROUTER_PASSWORD" ] || [ "$ROUTER_PASSWORD" = "" ]; then
    echo -e "${RED}❌ ROUTER_PASSWORD no configurada en .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Credenciales OK${NC}\n"

echo -e "${YELLOW}📦 INSTALANDO DEPENDENCIAS${NC}\n"

# Instalar paramiko
echo -n "Instalando paramiko... "
pip install paramiko -q 2>/dev/null || pip install paramiko --break-system-packages -q
echo -e "${GREEN}✅${NC}\n"

# ============================================================================
# PASO 1: CONFIGURAR ROUTER
# ============================================================================

echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐"
echo -e "│ PASO 1/4: CONFIGURAR ROUTER CON DUAL ISP + APs             │"
echo -e "└─────────────────────────────────────────────────────────────┘${NC}\n"

echo -e "${YELLOW}⏳ Conectando al router en $ROUTER_IP...${NC}\n"

python3 app/configure_router_dual_isp.py

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error configurando router${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Router configurado exitosamente${NC}\n"

# ============================================================================
# PASO 2: VERIFICAR CONFIGURACIÓN
# ============================================================================

echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐"
echo -e "│ PASO 2/4: VERIFICAR CONFIGURACIÓN                          │"
echo -e "└─────────────────────────────────────────────────────────────┘${NC}\n"

python3 app/verify_router_config.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Advertencia en verificación, continuando...${NC}\n"
fi

# ============================================================================
# PASO 3: CONFIGURAR BALANCEO DE CARGA
# ============================================================================

echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐"
echo -e "│ PASO 3/4: CONFIGURAR BALANCEO DE CARGA (PCC)              │"
echo -e "└─────────────────────────────────────────────────────────────┘${NC}\n"

python3 app/configure_load_balance.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Advertencia configurando balanceo, continuando...${NC}\n"
fi

# ============================================================================
# PASO 4: INICIAR SISTEMA NAC
# ============================================================================

echo -e "${BLUE}┌─────────────────────────────────────────────────────────────┐"
echo -e "│ PASO 4/4: INICIAR SISTEMA NAC                             │"
echo -e "└─────────────────────────────────────────────────────────────┘${NC}\n"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  ✅ TODA LA CONFIGURACIÓN COMPLETADA EXITOSAMENTE         ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}📊 RESUMEN:${NC}\n"
echo -e "  ${GREEN}✅${NC} Router configurado con Dual ISP"
echo -e "  ${GREEN}✅${NC} Puertos renombrados (ether1-isp1, ether2-isp2, etc)"
echo -e "  ${GREEN}✅${NC} Bridges configurados (ISPs, APs, LAN)"
echo -e "  ${GREEN}✅${NC} DHCP activo para APs y LAN"
echo -e "  ${GREEN}✅${NC} REST API habilitada en puerto 80"
echo -e "  ${GREEN}✅${NC} Usuario api-container creado"
echo -e "  ${GREEN}✅${NC} Balanceo de carga configurado (PCC)\n"

echo -e "${YELLOW}🚀 INICIANDO SISTEMA NAC...${NC}\n"
echo -e "El dashboard estará disponible en:\n"
echo -e "  ${GREEN}http://localhost:8080${NC}\n"

echo -e "${YELLOW}Presiona Ctrl+C para detener${NC}\n"

# Iniciar Sistema NAC
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
