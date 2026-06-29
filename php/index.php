<?php
// ── Front controller del NAC (reemplaza app/main.py de FastAPI) ──
require_once __DIR__ . '/lib/helpers.php';
require_once __DIR__ . '/api/auth.php';
require_once __DIR__ . '/api/users.php';
require_once __DIR__ . '/api/devices.php';
require_once __DIR__ . '/api/router.php';
require_once __DIR__ . '/api/traffic.php';
require_once __DIR__ . '/api/messages.php';
require_once __DIR__ . '/api/blocks.php';

// CORS (equivalente a CORSMiddleware allow_origins=*)
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: *, Authorization, X-Sync-Key, Content-Type');
// Evitar que Cloudflare/proxies cacheen respuestas dinámicas (sobre todo pull-script).
// Los estáticos (/static/*) los sirve LiteSpeed directo y sí pueden cachearse.
header('Cache-Control: no-store, no-cache, must-revalidate');

init_db();

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($method === 'OPTIONS') { http_response_code(204); exit; }
if ($method === 'HEAD') $method = 'GET';

// Path sin querystring
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$path = rawurldecode($path);
// Normalizar (sin barra final salvo raíz)
if ($path !== '/' && substr($path, -1) === '/') $path = rtrim($path, '/');

$routes = [];
function add(string $m, string $pattern, callable $h): void {
    global $routes;
    $regex = '#^' . preg_replace('#\{[^/]+\}#', '([^/]+)', $pattern) . '$#';
    $routes[] = [$m, $regex, $h];
}

// ── Sistema ──
add('GET', '/health', fn() => json_out(['status' => 'ok', 'version' => '2.0.0-php', 'service' => 'nac-system']));
add('GET', '/api/status', fn() => json_out(['status' => 'running', 'version' => '2.0.0-php', 'authentication' => 'enabled']));

// ── Auth ──
add('POST', '/api/auth/login', 'auth_login');
add('GET',  '/api/auth/me', 'auth_me');
add('POST', '/api/auth/logout', 'auth_logout');
add('POST', '/api/auth/change-password', 'auth_change_password');
add('GET',  '/api/auth/my-devices', 'auth_my_devices');
add('GET',  '/api/auth/registration-status', 'auth_registration_status');
add('POST', '/api/auth/register', 'auth_register');
add('GET',  '/api/auth/pending-users', 'auth_pending_users');
add('POST', '/api/auth/approve-user/{id}', 'auth_approve_user');
add('POST', '/api/auth/reject-user/{id}', 'auth_reject_user');
add('POST', '/api/auth/add-device', 'auth_add_device');

// ── Users (rutas específicas antes que /{id}) ──
add('GET',    '/api/users', 'users_list');
add('GET',    '/api/users/', 'users_list');
add('POST',   '/api/users', 'users_create');
add('POST',   '/api/users/', 'users_create');
add('PUT',    '/api/users/{id}/access', 'users_set_access');
add('PUT',    '/api/users/{id}/bandwidth', 'users_set_bandwidth');
add('PUT',    '/api/users/{id}/role', 'users_set_role');
add('GET',    '/api/users/{id}/devices', 'users_devices');
add('GET',    '/api/users/{id}', 'users_detail');
add('PUT',    '/api/users/{id}', 'users_update');
add('DELETE', '/api/users/{id}', 'users_delete');

// ── Devices (específicas antes que /{id}) ──
add('GET',    '/api/devices', 'devices_list');
add('GET',    '/api/devices/', 'devices_list');
add('POST',   '/api/devices', 'devices_create');
add('POST',   '/api/devices/', 'devices_create');
add('GET',    '/api/devices/pending/list', 'devices_pending_list');
add('GET',    '/api/devices/by-mac/{mac}', 'devices_by_mac');
add('GET',    '/api/devices/user/{id}/devices', 'devices_by_user');
add('PUT',    '/api/devices/{id}/approve', 'devices_approve');
add('PUT',    '/api/devices/{id}/reject', 'devices_reject');
add('GET',    '/api/devices/{id}', 'devices_get');
add('PUT',    '/api/devices/{id}', 'devices_update');
add('DELETE', '/api/devices/{id}', 'devices_delete');

// ── Router sync ──
add('GET',  '/api/router/pull-script', 'router_pull_script');
add('GET',  '/api/router/approved-macs', 'router_approved_macs');
add('GET',  '/api/router/approved-devices', 'router_approved_devices');
add('GET',  '/api/router/check-mac', 'router_check_mac');
add('POST', '/api/router/sync-approved-users', 'router_sync_approved_users');
add('GET',  '/api/router/authenticated-users', 'router_authenticated_users');

// ── Traffic ──
add('POST', '/api/traffic/report', 'traffic_report');
add('GET',  '/api/traffic/report-range', 'traffic_report_range');
add('GET',  '/api/traffic/live', 'traffic_live');
add('GET',  '/api/traffic/users', 'traffic_users');

// ── Messages (específicas antes que /{id}) ──
add('POST', '/api/messages', 'messages_send');
add('POST', '/api/messages/', 'messages_send');
add('GET',  '/api/messages', 'messages_list');
add('GET',  '/api/messages/', 'messages_list');
add('GET',  '/api/messages/unread-count', 'messages_unread_count');
add('PUT',  '/api/messages/{id}/read', 'messages_mark_read');
add('POST', '/api/messages/{id}/reply', 'messages_reply');
add('DELETE','/api/messages/{id}', 'messages_delete');

// ── Blocks ──
add('GET',    '/api/blocks/user/{id}', 'blocks_list_user');
add('POST',   '/api/blocks/user/{id}', 'blocks_add_user');
add('DELETE', '/api/blocks/{id}', 'blocks_remove');

// ── Frontend ──
add('GET', '/', 'serve_index');
add('GET', '/splash', 'splash_page');

function serve_index() {
    $f = __DIR__ . '/index.html';
    if (!is_file($f)) { http_response_code(404); echo 'index.html no encontrado'; exit; }
    header('Content-Type: text/html; charset=utf-8');
    readfile($f);
    exit;
}

function splash_page() {
    $mac = trim($_GET['mac'] ?? '');
    $ip  = trim($_GET['ip'] ?? '');
    $dst = trim($_GET['dst'] ?? '');
    $link = trim($_GET['link'] ?? '');

    if ($mac !== '') {
        $macU = strtoupper($mac);
        $dev = q_one(
            "SELECT d.id FROM devices d JOIN users u ON d.user_id = u.id
             WHERE UPPER(d.mac_address) = ? AND u.approval_status = 'approved' AND u.is_active = 1",
            [$macU]
        );
        if ($dev) {
            if ($link !== '') $base_login = $link;
            elseif (strpos($ip, '192.168.101.') === 0) $base_login = 'http://192.168.101.1:64872/login';
            else $base_login = 'http://192.168.100.1:64872/login';
            $redirect_to = $dst !== '' ? $dst : 'https://www.google.com';
            $username = strtolower(str_replace(':', '', $mac));
            $login_url = $base_login . '?username=' . rawurlencode($username)
                       . '&password=&dst=' . rawurlencode($redirect_to);
            $lu = htmlspecialchars($login_url, ENT_QUOTES);
            header('Content-Type: text/html; charset=utf-8');
            echo "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
               . "<meta http-equiv=\"refresh\" content=\"1;url=$lu\"><title>Acceso autorizado</title>"
               . "<style>body{font-family:-apple-system,sans-serif;text-align:center;padding:60px 20px;"
               . "background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;min-height:100vh;"
               . "display:flex;align-items:center;justify-content:center;}"
               . ".box{background:rgba(255,255,255,.15);border-radius:16px;padding:40px;max-width:400px;width:100%;}"
               . "h2{margin-bottom:12px;font-size:1.5rem;}p{opacity:.85;font-size:.9rem;}"
               . "a{color:#fff;opacity:.7;font-size:.85rem;}</style></head><body><div class=\"box\">"
               . "<h2>&#10003; Acceso autorizado</h2>"
               . "<p>Tu dispositivo está aprobado. Conectando a internet...</p>"
               . "<p><a href=\"$lu\">Haz clic aquí si no rediriges automáticamente</a></p></div>"
               . "<script>setTimeout(function(){window.location.replace(\"$lu\");},800);</script>"
               . "</body></html>";
            exit;
        }
    }
    $f = __DIR__ . '/splash.html';
    if (!is_file($f)) { http_response_code(404); echo 'splash.html no encontrado'; exit; }
    header('Content-Type: text/html; charset=utf-8');
    readfile($f);
    exit;
}

// ── Dispatch ──
foreach ($routes as [$m, $regex, $h]) {
    if ($m !== $method) continue;
    if (preg_match($regex, $path, $matches)) {
        array_shift($matches);
        try {
            call_user_func_array($h, $matches);
        } catch (Throwable $e) {
            abort(500, 'Internal error: ' . $e->getMessage());
        }
        exit;
    }
}

// Sin coincidencia: para rutas no-API, mostrar splash (captive portal). Para API, 404 JSON.
if (strpos($path, '/api') === 0) {
    abort(404, 'Not found');
}
splash_page();
