#!/bin/bash
set -e

echo "🚀 Iniciando deployment..."

# Paso 1: Asegurar que estamos en main
git checkout main 2>/dev/null || git switch -c main

# Paso 2: Verificar que todo está commitado
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️ Hay cambios sin commitear. Commitando..."
    git add -A
    git commit -m "Auto-commit before deployment" -m "Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>" || true
fi

# Paso 3: Push a main (Railway detectará el cambio y deployará automáticamente)
echo "📤 Pushing a GitHub..."
git push -u origin main --force-if-includes

echo ""
echo "✅ Push completado"
echo ""
echo "⏳ Railway debería detectar el push automáticamente y deployar"
echo ""
echo "Espera 2-3 minutos y luego ejecuta:"
echo "  railway logs -f"
echo ""
echo "Para ver la URL:"
echo "  railway open"

