# ===================================================================
# Script simple para crear usuario API
# Ejecutar en: /terminal del router o vía SSH
# ===================================================================

:log info "Removiendo usuario api-container anterior si existe..."
/user remove [find name=api-container]

:log info "Creando usuario api-container..."
/user add name=api-container password=NAC_MikroTik_2025 group=write

:log info "✓ Usuario creado"
:log info "Verificando..."
/user print where name=api-container

:log info "✓ Usuario api-container listo"
:log info "Credenciales: api-container / NAC_MikroTik_2025"
