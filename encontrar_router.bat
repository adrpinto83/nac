@echo off
REM Script para encontrar la IP real del router en Windows

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║  🔍 ENCONTRAR IP DEL ROUTER MIKROTIK                          ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

echo 📋 PASO 1: Ver tu configuración de red
echo ════════════════════════════════════════
echo.

ipconfig /all

echo.
echo 📋 PASO 2: Buscar el Gateway (Router)
echo ════════════════════════════════════════
echo.

echo Tu Gateway (Router) es:
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| find "Puerta de enlace predeterminada"') do (
    set "gateway=%%A"
)

if defined gateway (
    echo    %gateway%
    echo.
    echo Probando ping a tu router...
    ping -n 1 %gateway%
) else (
    echo    No se encontró gateway
    echo.
)

echo.
echo 📋 PASO 3: Buscar todos los dispositivos en la red
echo ════════════════════════════════════════════════════
echo.
echo Buscando dispositivos MikroTik en la red (esto puede tomar 30 segundos)...
echo.

REM Obtener la red local
for /f "tokens=1,2,3,4 delims=." %%a in ('ipconfig ^| findstr /R "IPv4"') do (
    set "ip=%%a.%%b.%%c.%%d"
    set "network=%%a.%%b.%%c"
)

if defined network (
    echo Tu red es: %network%.0/24
    echo.
    echo Escaneando dispositivos en %network%.0-255...
    echo.

    REM Probar ping a IPs comunes del router
    for /L %%i in (1,1,20) do (
        ping -n 1 -w 100 %network%.%%i >nul 2>&1
        if !errorlevel! equ 0 (
            echo ✓ Dispositivo encontrado: %network%.%%i
            REM Obtener nombre del host
            for /f "tokens=1,2,3,4,5" %%A in ('nbtstat -a %network%.%%i 2^>nul') do (
                if not "%%A"=="Local" (
                    echo    Nombre: %%A
                )
            )
        )
    )
)

echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 📝 INFORMACIÓN IMPORTANTE:
echo.
echo 1. Anota la IP que encontraste (normalmente es .1 o .254)
echo.
echo 2. En la carpeta del proyecto, edita el archivo .env:
echo    - Abre: .env
echo    - Busca: ROUTER_IP=
echo    - Cambia a: ROUTER_IP=XXX.XXX.XXX.XXX (tu IP)
echo    - Guarda
echo.
echo 3. Prueba conexión:
echo    ping XXX.XXX.XXX.XXX
echo.
echo 4. Si responde, ejecuta:
echo    bash ejecutar_todo.sh
echo.
echo ════════════════════════════════════════════════════════════════
echo.
pause
