#!/bin/bash
# Script para ejecutar el Sistema MikroTik NAC localmente

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}MikroTik NAC System - Inicio${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Activar virtualenv
echo -e "\n${YELLOW}[1/3]${NC} Activando virtualenv..."
source venv/bin/activate

# Crear directorio data si no existe
echo -e "${YELLOW}[2/3]${NC} Preparando directorios..."
mkdir -p data logs

# Iniciar la aplicación
echo -e "${YELLOW}[3/3]${NC} Iniciando servidor..."
echo -e "${GREEN}✓ Servidor iniciará en http://localhost:8080${NC}"
echo -e "${GREEN}✓ API docs: http://localhost:8080/docs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
