# Cutover del router MikroTik: Railway -> Hostinger
# Ejecutar SOLO cuando https://wifi.jadsstudio.com responda (subdominio + SSL activos en hPanel).
# Apunta el script nac-sync al nuevo pull-script PHP (que ya trae el fix del bug de consumo).

/system script set [find name=nac-sync] source="/tool/fetch url=\"https://wifi.jadsstudio.com/api/router/pull-script?key=nac-sync-2024\" mode=https http-method=get output=file dst-path=nac-sync.rsc check-certificate=no\r\n/import file-name=nac-sync.rsc verbose=no\r\n:log info \"NAC-AUTO: sync OK\""

# Forzar una corrida inmediata para validar:
/system script run [find name=nac-sync]
