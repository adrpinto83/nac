# run_sync_windows.ps1
# Ejecutar desde PowerShell de Windows (NO desde WSL) cuando WSL no tiene ruta al router.
# Windows tiene acceso directo a la red MikroTik.
#
# Uso:
#   .\run_sync_windows.ps1              # sync una vez
#   .\run_sync_windows.ps1 -Loop       # sync cada 60s (mantener corriendo)
#   .\run_sync_windows.ps1 -FixIp 192.168.100.6  # fix inmediato para un dispositivo

param(
    [switch]$Loop,
    [string]$FixIp = ""
)

# Buscar Python en Windows
$python = $null
foreach ($candidate in @("python", "python3", "py")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python 3") {
            $python = $candidate
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Error "Python 3 no encontrado en Windows. Instala Python desde python.org"
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentPath = Join-Path $scriptDir "sync_agent.py"

if ($FixIp) {
    Write-Host "Aplicando fix para dispositivo $FixIp ..."
    & $python $agentPath --fix-ip $FixIp
} elseif ($Loop) {
    Write-Host "Iniciando sync loop (Ctrl+C para detener) ..."
    & $python $agentPath --loop
} else {
    Write-Host "Ejecutando sync una vez ..."
    & $python $agentPath
}
