<?php
// /api/router/*  — port de app/routers/router_sync.py
// NOTA: el sync real con el MikroTik es por pull-script (el router descarga e importa cada 60s).
// Las llamadas directas al router NO funcionan desde la nube (router en LAN privada).

function _approved_devices_rows() {
    // Devuelve [mac, download_mbps, upload_mbps] de dispositivos aprobados y vigentes.
    $now = gmdate('Y-m-d\TH:i:s');
    return q_all(
        "SELECT d.mac_address AS mac, u.download_mbps AS dl, u.upload_mbps AS ul
         FROM devices d JOIN users u ON d.user_id = u.id
         WHERE u.approval_status = 'approved' AND u.is_active = 1
           AND COALESCE(d.approval_status,'approved') = 'approved'
           AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)",
        [$now]
    );
}

function router_pull_script() {
    if (($_GET['key'] ?? '') !== SYNC_KEY) abort(403, 'Invalid key');

    $rows = _approved_devices_rows();
    // devices[MAC] = [dl, ul]
    $devices = [];
    foreach ($rows as $r) {
        if (!empty($r['mac'])) $devices[strtoupper($r['mac'])] = [$r['dl'], $r['ul']];
    }

    $ts = gmdate('Y-m-d H:i') . ' UTC';
    $base = PUBLIC_BASE_URL;
    $sync = SYNC_KEY;

    $L = [];
    $L[] = "# NAC-SYNC $ts | " . count($devices) . " dispositivos";
    $L[] = "";

    // --- Acceso: ip-binding type=bypassed por MAC aprobada ---
    //     Es el mecanismo confiable: el hotspot deja de interceptar (NAT/DNS/HTTP) esa MAC
    //     por completo. NO depende del MAC-auth del hotspot (que falla si el dispositivo ya
    //     estaba conectado como host no autenticado al momento de aprobarlo).
    //     Los hosts bypassed igual reportan bytes (flag P), así que el consumo se sigue contando.
    $L[] = "# Acceso libre: ip-binding bypassed para MACs aprobadas (upsert)";
    foreach (array_keys($devices) as $mac) {
        $L[] = ":do { /ip hotspot ip-binding add mac-address=\"$mac\" type=bypassed comment=\"NAC:$mac\" } "
             . "on-error={ /ip hotspot ip-binding set [find mac-address=\"$mac\"] type=bypassed }";
    }
    if ($devices) {
        $notin = implode(' ', array_map(fn($m) => "mac-address!=\"$m\"", array_keys($devices)));
        $L[] = "# Eliminar ip-bindings NAC obsoletos (revocados/eliminados)";
        $L[] = "/ip hotspot ip-binding remove [find comment~\"NAC:\" $notin]";
    } else {
        $L[] = "# Sin dispositivos aprobados — eliminar todos los ip-bindings NAC";
        $L[] = '/ip hotspot ip-binding remove [find comment~"NAC:"]';
    }
    $L[] = "";
    $L[] = "# Limpiar hotspot users NAC antiguos (el acceso ahora es por ip-binding)";
    $L[] = '/ip/hotspot/user remove [find comment~"NAC:"]';

    // --- Forward filter: accept por MAC aprobada + bypass established ---
    $L[] = "";
    $L[] = "# Forward filter rules: eliminar obsoletos y re-agregar aprobados";
    $L[] = '/ip/firewall/filter remove [find chain=forward comment~"NAC:" action=accept]';
    $L[] = ':local fid ""';
    $L[] = ':foreach r in=[/ip/firewall/filter find chain=forward action=jump jump-target=hs-unauth dynamic=yes] do={ :set fid $r }';
    foreach (array_keys($devices) as $mac) {
        $L[] = ":do { /ip/firewall/filter add chain=forward src-mac-address=\"$mac\" action=accept comment=\"NAC:$mac\" place-before=\$fid } "
             . "on-error={ :do { /ip/firewall/filter add chain=forward src-mac-address=\"$mac\" action=accept comment=\"NAC:$mac\" } on-error={} }";
    }

    $L[] = "";
    $L[] = "# Bypass established/related";
    $L[] = '/ip/firewall/filter remove [find chain=forward comment="bypass-established"]';
    $L[] = ':do { /ip/firewall/filter add chain=forward connection-state=established,related action=accept comment="bypass-established" place-before=$fid } '
         . 'on-error={ :do { /ip/firewall/filter add chain=forward connection-state=established,related action=accept comment="bypass-established" } on-error={} }';

    // --- Bloqueos de sitios por usuario (DNS estático -> 127.0.0.1) ---
    $L[] = "";
    $L[] = "# Bloqueos de sitios (DNS estatico). Se recrean en cada sync.";
    $L[] = '/ip/dns/static remove [find comment~"NAC-BLOCK"]';
    $blocks = q_all(
        "SELECT DISTINCT b.domain AS domain
         FROM user_site_blocks b
         JOIN devices d ON d.user_id = b.user_id
         JOIN users u ON u.id = b.user_id
         WHERE u.approval_status='approved' AND u.is_active=1"
    );
    foreach ($blocks as $bk) {
        $dom = $bk['domain'];
        if ($dom === '') continue;
        $L[] = ":do { /ip/dns/static add name=\"$dom\" address=127.0.0.1 comment=\"NAC-BLOCK\" } on-error={}";
    }

    // --- QoS: simple queue por MAC con límite (resuelve la IP actual en runtime) ---
    $L[] = "";
    $L[] = "# QoS: limpiar queues NAC y recrear para MACs con limite";
    $L[] = '/queue simple remove [find comment~"NAC:"]';
    foreach ($devices as $mac => $lim) {
        [$dl, $ul] = $lim;
        if (!$dl && !$ul) continue;
        // queue simple max-limit = "subida/bajada" del target (cliente)
        $maxlim = ((int)$ul ?: 0) . 'M/' . ((int)$dl ?: 0) . 'M';
        $L[] = ":foreach hh in=[/ip hotspot host find where mac-address=\"$mac\"] do={";
        $L[] = "  :local qip [/ip hotspot host get \$hh address]";
        $L[] = "  :if (\$qip != \"\") do={";
        $L[] = "    :do { /queue simple add name=\"NAC:$mac\" target=\$qip max-limit=$maxlim comment=\"NAC:$mac\" } "
             . "on-error={ /queue simple set [find comment=\"NAC:$mac\"] target=\$qip max-limit=$maxlim }";
        $L[] = "  }";
        $L[] = "}";
    }

    // --- Reporte de tráfico (recorre /ip hotspot host y hace POST) ---
    $L[] = "";
    $L[] = "# Reportar trafico via /ip hotspot host";
    // NOTA: RouterOS NO permite guion bajo en nombres de variable -> usar camelCase.
    $L[] = ':local nacSessions ""';
    $L[] = ':local nacSep ""';
    $L[] = ':foreach h in=[/ip hotspot host find] do={';
    $L[] = '  :local nacM  [/ip hotspot host get $h mac-address]';
    $L[] = '  :local nacA  [/ip hotspot host get $h address]';
    $L[] = '  :local nacBi [/ip hotspot host get $h bytes-in]';
    $L[] = '  :local nacBo [/ip hotspot host get $h bytes-out]';
    $L[] = '  :if ($nacA != "") do={';
    $L[] = '    :set nacSessions ($nacSessions . $nacSep . "{\"user\":\"" . $nacM . "\",\"address\":\"" . $nacA . "\",\"mac_address\":\"" . $nacM . "\",\"bytes_in\":" . $nacBi . ",\"bytes_out\":" . $nacBo . ",\"uptime\":\"\"}")';
    $L[] = '    :set nacSep ","';
    $L[] = '  }';
    $L[] = '}';
    $L[] = ':if ($nacSessions != "") do={';
    $L[] = '  :local nacBody ("{\"sessions\":[" . $nacSessions . "]}")';
    $L[] = "  :do { /tool fetch url=\"$base/api/traffic/report\" http-method=post http-header-field=\"Content-Type:application/json,X-Sync-Key:$sync\" http-data=\$nacBody mode=https check-certificate=no output=none } on-error={}";
    $L[] = '}';
    $L[] = "";
    $L[] = ':log info "NAC-SYNC: completo"';

    header('Content-Type: text/plain; charset=utf-8');
    echo implode("\n", $L) . "\n";
    exit;
}

function router_approved_macs() {
    if (($_GET['key'] ?? '') !== SYNC_KEY) abort(403, 'Invalid key');
    $rows = _approved_devices_rows();
    $macs = [];
    foreach ($rows as $r) if (!empty($r['mac'])) $macs[] = $r['mac'];
    header('Content-Type: text/plain; charset=utf-8');
    echo implode("\n", $macs) . "\n";
    exit;
}

function router_approved_devices() {
    if (($_GET['key'] ?? '') !== SYNC_KEY) abort(403, 'Invalid key');
    $rows = _approved_devices_rows();
    $out = [];
    foreach ($rows as $r) {
        if (!empty($r['mac'])) {
            $out[] = ['mac' => $r['mac'],
                      'download_mbps' => $r['dl'] !== null ? (int)$r['dl'] : null,
                      'upload_mbps' => $r['ul'] !== null ? (int)$r['ul'] : null];
        }
    }
    json_out($out);
}

function router_check_mac() {
    $mac = trim($_GET['mac'] ?? '');
    if (!$mac) json_out(['approved' => false]);
    $macU = strtoupper($mac);
    $now = gmdate('Y-m-d\TH:i:s');
    $row = q_one(
        "SELECT d.id FROM devices d JOIN users u ON d.user_id = u.id
         WHERE UPPER(d.mac_address) = ? AND u.approval_status='approved' AND u.is_active=1
           AND COALESCE(d.approval_status,'approved')='approved'
           AND (u.access_expires_at IS NULL OR u.access_expires_at > ?)",
        [$macU, $now]
    );
    json_out(['approved' => (bool)$row, 'mac' => $macU]);
}

// Endpoints admin que dependían del cliente MikroTik directo: en el modelo pull-script
// no aplican desde la nube. Se responde de forma informativa para no romper el frontend.
function router_sync_approved_users() {
    require_admin();
    json_out(['status' => 'success', 'added' => [], 'removed' => [], 'errors' => [],
              'message' => 'El router se auto-sincroniza vía pull-script cada 60s.']);
}
function router_authenticated_users() {
    require_admin();
    $rows = q_all("SELECT mac_address, address, bytes_in, bytes_out FROM live_sessions ORDER BY reported_at DESC");
    json_out(['status' => 'success', 'count' => count($rows), 'users' => $rows]);
}
