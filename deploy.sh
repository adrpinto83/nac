#!/bin/bash
# deploy.sh — Script de despliegue del container NAC en MikroTik

set -e

# Configuración
ROUTER_IP="192.168.88.1"
ROUTER_USER="admin"
CONTAINER_NAME="app-nac"
IMAGE_NAME="nac:1.0"
IMAGE_FILENAME="nac-1.0.tar"

echo "=========================================="
echo "MikroTik NAC - Script de Despliegue"
echo "=========================================="

# Step 1: Build Docker image
echo ""
echo "[1/5] Construyendo imagen Docker..."
docker build -t $IMAGE_NAME .

# Step 2: Export image
echo ""
echo "[2/5] Exportando imagen a TAR..."
docker save $IMAGE_NAME -o $IMAGE_FILENAME
IMAGE_SIZE=$(ls -lh $IMAGE_FILENAME | awk '{print $5}')
echo "✓ Imagen exportada: $IMAGE_FILENAME ($IMAGE_SIZE)"

# Step 3: Upload to router
echo ""
echo "[3/5] Subiendo imagen al router ($ROUTER_IP)..."
scp -o StrictHostKeyChecking=no $IMAGE_FILENAME $ROUTER_USER@$ROUTER_IP:/tmp/

# Step 4: Load image in container
echo ""
echo "[4/5] Cargando imagen en RouterOS..."
ssh -o StrictHostKeyChecking=no $ROUTER_USER@$ROUTER_IP << 'EOF'

# Detener container si existe
/container/stop $CONTAINER_NAME 2>/dev/null || true
/container/remove $CONTAINER_NAME 2>/dev/null || true

# Cargar nueva imagen
/container/import file=/tmp/nac-1.0.tar name=nac:1.0

echo "✓ Imagen cargada exitosamente"
EOF

# Step 5: Create and start container
echo ""
echo "[5/5] Creando e iniciando container..."
ssh -o StrictHostKeyChecking=no $ROUTER_USER@$ROUTER_IP << 'EOF'

/container/add name=$CONTAINER_NAME \
    image=$IMAGE_NAME \
    interface=veth1 \
    root-dir=/container-root \
    envlist=PATH,LD_LIBRARY_PATH,LANG

/container/start $CONTAINER_NAME

echo "✓ Container iniciado"

# Esperar a que arranche
sleep 3

# Verificar estado
/container/print detail

EOF

# Clean up
echo ""
echo "=========================================="
echo "✓ Despliegue completado exitosamente"
echo "=========================================="
echo ""
echo "Panel accesible en: http://192.168.88.1:8080"
echo "Login por defecto: admin / admin123"
echo ""
echo "Para ver logs del container:"
echo "  ssh admin@192.168.88.1"
echo "  /container/print detail"
echo "  /container/shell app-nac"
echo ""

# Clean temporary files
rm -f $IMAGE_FILENAME
