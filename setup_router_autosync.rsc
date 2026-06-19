# ============================================================
#  NAC AUTO-SYNC — Configurar en el router MikroTik (una sola vez)
#  Pegar en WinBox → New Terminal  o  ssh admin@192.168.88.1
#
#  Resultado: el router descarga y aplica cambios de Railway
#  cada 60 segundos, SIN necesitar ningún PC.
# ============================================================

:local RAILWAY_URL "https://nac-production.up.railway.app/api/router/pull-script?key=nac-sync-2024"
:local SCRIPT_NAME "nac-sync"
:local SCHED_NAME  "nac-auto-sync"

# ── 1. Crear script en el router ─────────────────────────────────────────────
:if ([:len [/system/script find name=$SCRIPT_NAME]] > 0) do={
    /system/script remove [find name=$SCRIPT_NAME]
    :put "Script anterior eliminado"
}

/system/script add name=$SCRIPT_NAME \
    source=":do {\
\n    :local r [/tool/fetch url=\"$RAILWAY_URL\" mode=https http-method=get output=user as-value check-certificate=no]\
\n    :local sc (\$r->\"data\")\
\n    [:parse \$sc]\
\n    :log info \"NAC-AUTO: sync OK\"\
\n} on-error={\
\n    :log error \"NAC-AUTO: error al descargar script de Railway\"\
\n}"

:put "Script '$SCRIPT_NAME' creado"

# ── 2. Crear tarea en el scheduler ───────────────────────────────────────────
:if ([:len [/system/scheduler find name=$SCHED_NAME]] > 0) do={
    /system/scheduler remove [find name=$SCHED_NAME]
}

/system/scheduler add \
    name=$SCHED_NAME \
    interval=00:01:00 \
    on-event=$SCRIPT_NAME \
    comment="NAC: sincroniza MACs aprobadas desde Railway cada minuto"

:put "Scheduler '$SCHED_NAME' configurado (cada 60s)"

# ── 3. Ejecutar inmediatamente (primer sync) ──────────────────────────────────
:put "Ejecutando primer sync..."
/system/script run $SCRIPT_NAME

:put "============================================"
:put "LISTO: El router sincronizara automaticamente"
:put "cada 60 segundos sin necesitar ningun PC."
:put "Ver log: /log print where topics~\"NAC\""
:put "============================================"
