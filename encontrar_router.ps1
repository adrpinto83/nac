# Script PowerShell para encontrar el router MikroTik

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "║  🔍 ENCONTRAR IP DEL ROUTER MIKROTIK                          ║" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PASO 1: Ver configuración de red
# ============================================================================

Write-Host "📋 PASO 1: Tu configuración de red" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

$networkConfig = Get-NetIPConfiguration -Detailed

foreach ($config in $networkConfig) {
    if ($config.IPv4DefaultGateway) {
        Write-Host "Interfaz: $($config.InterfaceAlias)" -ForegroundColor Green
        Write-Host "  IP: $($config.IPv4Address.IPAddress)" -ForegroundColor Cyan
        Write-Host "  Máscara: $($config.IPv4Address.PrefixLength)" -ForegroundColor Cyan
        Write-Host "  Gateway: $($config.IPv4DefaultGateway.NextHopAddress)" -ForegroundColor Cyan
        Write-Host ""
    }
}

# ============================================================================
# PASO 2: Obtener información de la red
# ============================================================================

Write-Host "📋 PASO 2: Buscando dispositivos en la red..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

# Obtener gateway
$gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object -First 1).NextHop

if ($gateway) {
    Write-Host "Tu Gateway (router): $gateway" -ForegroundColor Green
    Write-Host "Probando ping..." -ForegroundColor Cyan

    $ping = Test-Connection -ComputerName $gateway -Count 1 -Quiet
    if ($ping) {
        Write-Host "✅ Gateway responde a ping" -ForegroundColor Green
        Write-Host ""
        Write-Host "Posible solución:" -ForegroundColor Yellow
        Write-Host "1. Edita el archivo .env"
        Write-Host "2. Cambia ROUTER_IP a: $gateway"
        Write-Host "3. Guarda"
        Write-Host "4. Ejecuta: bash ejecutar_todo.sh"
        Write-Host ""
    } else {
        Write-Host "❌ Gateway no responde" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "No se encontró gateway" -ForegroundColor Red
}

# ============================================================================
# PASO 3: Buscar IPs comunes de routers
# ============================================================================

Write-Host "📋 PASO 3: Buscando IPs comunes de router..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

# IPs típicas de routers
$tipicalRouters = @(
    "192.168.1.1",
    "192.168.88.1",
    "192.168.0.1",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.254",
    "192.168.88.254"
)

Write-Host "Probando IPs típicas..." -ForegroundColor Cyan
Write-Host ""

foreach ($ip in $tipicalRouters) {
    $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($ping) {
        Write-Host "✅ Encontrado: $ip" -ForegroundColor Green

        # Intentar obtener nombre
        try {
            $hostname = [System.Net.Dns]::GetHostEntry($ip).HostName
            Write-Host "   Nombre: $hostname" -ForegroundColor Cyan
        } catch {
            Write-Host "   (sin nombre disponible)" -ForegroundColor Gray
        }
    }
}

Write-Host ""

# ============================================================================
# PASO 4: Escanear rango de IPs
# ============================================================================

Write-Host "📋 PASO 4: Escaneando rango de IPs (esto toma ~30 segundos)..." -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""

# Obtener red local
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" })[0].IPAddress
if ($localIP) {
    $parts = $localIP.Split(".")
    $network = "$($parts[0]).$($parts[1]).$($parts[2])"

    Write-Host "Tu red local es: $network.0/24" -ForegroundColor Cyan
    Write-Host "Escaneando $network.1 - $network.254..." -ForegroundColor Cyan
    Write-Host ""

    $jobs = @()

    # Crear jobs para parallelizar el ping
    for ($i = 1; $i -le 254; $i++) {
        $ip = "$network.$i"
        $jobs += Start-Job -ScriptBlock {
            param($ip)
            $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
            if ($ping) {
                return $ip
            }
        } -ArgumentList $ip
    }

    # Esperar a que terminen
    $results = $jobs | Wait-Job | Receive-Job

    Write-Host "Dispositivos encontrados:" -ForegroundColor Green
    Write-Host ""

    foreach ($ip in ($results | Sort-Object)) {
        Write-Host "  ✓ $ip" -ForegroundColor Green
    }

    Write-Host ""
}

# ============================================================================
# PASO 5: Instrucciones finales
# ============================================================================

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📝 ¿QUÉ HACER AHORA?" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Si encontraste un dispositivo que responde:" -ForegroundColor Yellow
Write-Host "   • Esa probablemente es tu IP del router" -ForegroundColor Cyan
Write-Host "   • Abre navegador: http://XXX.XXX.XXX.XXX" -ForegroundColor Cyan
Write-Host "   • Verifica que es MikroTik" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. Edita el archivo .env:" -ForegroundColor Yellow
Write-Host "   • Abre archivo: .env" -ForegroundColor Cyan
Write-Host "   • Busca: ROUTER_IP=192.168.88.1" -ForegroundColor Cyan
Write-Host "   • Cambia a tu IP: ROUTER_IP=XXX.XXX.XXX.XXX" -ForegroundColor Cyan
Write-Host "   • Guarda" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Verifica conectividad:" -ForegroundColor Yellow
Write-Host "   • ping XXX.XXX.XXX.XXX" -ForegroundColor Cyan
Write-Host "   • ssh admin@XXX.XXX.XXX.XXX" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Ejecuta la configuración:" -ForegroundColor Yellow
Write-Host "   • bash ejecutar_todo.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
