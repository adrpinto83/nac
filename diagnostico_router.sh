#!/bin/bash

###############################################################################
#                                                                             #
#  🔍 SCRIPT DE DIAGNÓSTICO - Identificar problemas de conexión              #
#                                                                             #
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  🔍 DIAGNÓSTICO DE CONECTIVIDAD - ROUTER MIKROTIK             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# ============================================================================
# 1. VERIFICAR IP LOCAL
# ============================================================================

echo -e "${YELLOW}1️⃣  VERIFICAR IP LOCAL DE TU PC${NC}\n"

echo "Tu interfaz de red:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    ip addr show | grep "inet " | grep -v "127.0.0.1"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    ifconfig | grep "inet " | grep -v "127.0.0.1"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    ipconfig | grep "IPv4"
fi

echo -e "\n${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "Tu IP debe estar en el rango 192.168.88.x"
echo "Si NO es así, el router está en una red diferente\n"

# ============================================================================
# 2. PING AL ROUTER
# ============================================================================

echo -e "${YELLOW}2️⃣  PROBAR PING AL ROUTER (192.168.88.1)${NC}\n"

if ping -c 3 192.168.88.1 2>/dev/null || ping -n 3 192.168.88.1 2>/dev/null; then
    echo -e "${GREEN}✅ ROUTER RESPONDE${NC}\n"
else
    echo -e "${RED}❌ ROUTER NO RESPONDE A PING${NC}\n"
    echo -e "${YELLOW}POSIBLES SOLUCIONES:${NC}"
    echo "1. Verificar que el router está encendido"
    echo "2. Verificar que estás en la misma red WiFi/Ethernet"
    echo "3. Verificar que el cable Ethernet está conectado"
    echo "4. Hacer ping a 192.168.88.1 manualmente"
    echo ""
fi

# ============================================================================
# 3. VERIFICAR PUERTO SSH
# ============================================================================

echo -e "${YELLOW}3️⃣  PROBAR PUERTO SSH (22) DEL ROUTER${NC}\n"

if command -v nc &> /dev/null; then
    if nc -zv 192.168.88.1 22 2>/dev/null; then
        echo -e "${GREEN}✅ PUERTO SSH (22) ABIERTO${NC}\n"
    else
        echo -e "${RED}❌ PUERTO SSH (22) NO RESPONDE${NC}\n"
    fi
elif command -v timeout &> /dev/null; then
    if timeout 2 bash -c 'echo > /dev/tcp/192.168.88.1/22' 2>/dev/null; then
        echo -e "${GREEN}✅ PUERTO SSH (22) ABIERTO${NC}\n"
    else
        echo -e "${RED}❌ PUERTO SSH (22) NO RESPONDE${NC}\n"
    fi
else
    echo -e "${YELLOW}⚠️  No se puede verificar puerto SSH automáticamente${NC}"
    echo "Prueba manualmente: ssh admin@192.168.88.1\n"
fi

# ============================================================================
# 4. VERIFICAR PUERTO REST API
# ============================================================================

echo -e "${YELLOW}4️⃣  PROBAR PUERTO REST API (80) DEL ROUTER${NC}\n"

if command -v curl &> /dev/null; then
    if curl -s -m 3 http://192.168.88.1 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PUERTO REST API (80) ABIERTO${NC}\n"
    else
        echo -e "${RED}❌ PUERTO REST API (80) NO RESPONDE${NC}\n"
        echo "Pero puede haber datos más específicos:\n"
        curl -v -m 3 http://192.168.88.1 2>&1 | head -20
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  curl no instalado, instálalo para probar REST API${NC}\n"
fi

# ============================================================================
# 5. INTENTAR CONEXIÓN SSH
# ============================================================================

echo -e "${YELLOW}5️⃣  INTENTAR CONEXIÓN SSH AL ROUTER${NC}\n"

echo "Intentando: ssh admin@192.168.88.1"
echo "(Presiona Ctrl+C para cancelar si se cuelga)"
echo ""

timeout 5 ssh -v -o ConnectTimeout=3 -o StrictHostKeyChecking=no admin@192.168.88.1 "echo OK" 2>&1 | head -20

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CONEXIÓN SSH EXITOSA${NC}\n"
else
    echo -e "${RED}❌ NO SE PUEDE CONECTAR VIA SSH${NC}\n"
fi

# ============================================================================
# 6. INFORMACIÓN DEL ROUTER
# ============================================================================

echo -e "${YELLOW}6️⃣  INFORMACIÓN DEL ROUTER${NC}\n"

echo "Para verificar la configuración actual del router:"
echo ""
echo "  1. Abre navegador: http://192.168.88.1"
echo "  2. O usa WebFig (interfaz web)"
echo "  3. O conecta via SSH: ssh admin@192.168.88.1"
echo ""

# ============================================================================
# 7. CHECKLIST DE SOLUCIÓN
# ============================================================================

echo -e "${YELLOW}📋 CHECKLIST DE SOLUCIÓN${NC}\n"

echo "Si el ping FALLÓ:"
echo "  [ ] ¿El router está encendido?"
echo "  [ ] ¿Estás conectado a la misma red (WiFi o Ethernet)?"
echo "  [ ] ¿La IP de tu PC es 192.168.88.x?"
echo "  [ ] ¿Has probado conectar via cable Ethernet?"
echo ""

echo "Si SSH FALLA pero ping OK:"
echo "  [ ] ¿SSH está habilitado en el router?"
echo "  [ ] En WebFig: System > SSH Server"
echo "  [ ] Verificar que SSH Server está ENABLED"
echo ""

echo "Si REST API FALLA:"
echo "  [ ] ¿REST API está habilitada?"
echo "  [ ] En WebFig: IP > Services > REST API"
echo "  [ ] Verificar que REST API está habilitada en puerto 80"
echo ""

# ============================================================================
# 8. ALTERNATIVAS SI FALLA CONECTIVIDAD
# ============================================================================

echo -e "${YELLOW}🔧 ALTERNATIVAS SI NO HAY CONECTIVIDAD${NC}\n"

echo "Si el router no está en 192.168.88.1:"
echo ""
echo "1. Buscar IP real del router:"
echo "   - Windows: ipconfig /all"
echo "   - Linux/macOS: ifconfig o ip addr"
echo "   - Buscar 'Default Gateway' o 'Router'"
echo ""
echo "2. Una vez encontrada la IP, editar .env:"
echo "   ROUTER_IP=<la-ip-real>"
echo ""

# ============================================================================
# FINAL
# ============================================================================

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📞 SI PERSISTE EL PROBLEMA:${NC}"
echo "1. Anota los resultados de este diagnóstico"
echo "2. Verifica que el router está online"
echo "3. Reinicia el router (apagar y encender)"
echo "4. Intenta nuevamente"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
