<?php
// /api/traffic/*  — port de app/routers/traffic.py

function traffic_report() {
    if (header_val('x-sync-key') !== SYNC_KEY) abort(403, 'Clave de sincronización inválida');
    $b = body_json();
    $sessions = $b['sessions'] ?? [];
    $saved = 0;
    $db = db();
    $db->beginTransaction();
    try {
        // refrescar cache de sesiones en vivo
        $db->exec("DELETE FROM live_sessions");
        foreach ($sessions as $s) {
            // Contadores acumulados del router (/ip hotspot host):
            //   bytes-in  = recibido DEL cliente  = SUBIDA del cliente
            //   bytes-out = enviado AL cliente    = BAJADA del cliente
            $rin  = max(0, (int)($s['bytes_in'] ?? 0));   // subida acumulada
            $rout = max(0, (int)($s['bytes_out'] ?? 0));  // bajada acumulada
            $mac = strtoupper(trim($s['mac_address'] ?? ($s['user'] ?? '')));
            if ($mac !== '') {
                q("INSERT OR REPLACE INTO live_sessions (mac_address, user, address, uptime, bytes_in, bytes_out, reported_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                   [$mac, $s['user'] ?? '', $s['address'] ?? '', $s['uptime'] ?? '', $rin, $rout]);
            }
            if ($mac === '') continue;
            $dev = q_one("SELECT user_id FROM devices WHERE UPPER(mac_address) = ?", [$mac]);
            if (!$dev) continue;

            // Delta real desde el último reporte; si el contador bajó (host recreado), el delta es el valor actual.
            $prev = q_one("SELECT last_in, last_out FROM mac_counter WHERE mac_address = ?", [$mac]);
            $lin  = $prev ? (int)$prev['last_in']  : 0;
            $lout = $prev ? (int)$prev['last_out'] : 0;
            $dUp   = ($rin  >= $lin)  ? ($rin  - $lin)  : $rin;   // subida incremental
            $dDown = ($rout >= $lout) ? ($rout - $lout) : $rout;  // bajada incremental

            q("INSERT OR REPLACE INTO mac_counter (mac_address, last_in, last_out, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)", [$mac, $rin, $rout]);

            if ($dUp > 0 || $dDown > 0) {
                // bytes_down = bajada, bytes_up = subida (mapeo corregido)
                q("INSERT INTO traffic_usage (user_id, bytes_down, bytes_up) VALUES (?, ?, ?)",
                  [$dev['user_id'], $dDown, $dUp]);
                q("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", [$dev['user_id']]);
                $saved++;
            }
        }
        $db->commit();
    } catch (Throwable $e) {
        $db->rollBack();
        abort(500, 'report error: ' . $e->getMessage());
    }
    json_out(['ok' => true, 'saved' => $saved]);
}

function traffic_live() {
    if (($_GET['key'] ?? '') !== SYNC_KEY) abort(403, 'Clave inválida');
    $rows = q_all("SELECT user, address, mac_address, uptime, bytes_in, bytes_out FROM live_sessions");
    $last = q_one("SELECT MAX(reported_at) AS t FROM live_sessions");
    $sessions = [];
    foreach ($rows as $r) {
        $sessions[] = ['user' => $r['user'], 'address' => $r['address'],
                       'mac_address' => $r['mac_address'], 'uptime' => $r['uptime'],
                       'bytes_in' => (int)$r['bytes_in'], 'bytes_out' => (int)$r['bytes_out']];
    }
    json_out(['last_report_at' => $last['t'] ?? null,
              'session_count' => count($sessions), 'sessions' => $sessions]);
}

function _valid_date($d, $default) {
    return (is_string($d) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) ? $d : $default;
}

// GET /api/traffic/report-range?from=YYYY-MM-DD&to=YYYY-MM-DD[&user_id=N]
// Reporte de consumo por empleado en un rango de fechas. Solo admin.
function traffic_report_range() {
    require_admin();
    $to   = _valid_date($_GET['to']   ?? null, gmdate('Y-m-d'));
    $from = _valid_date($_GET['from'] ?? null, gmdate('Y-m-d', time() - 29 * 86400));
    if ($from > $to) { $tmp = $from; $from = $to; $to = $tmp; }
    $user_id = isset($_GET['user_id']) && $_GET['user_id'] !== '' ? (int)$_GET['user_id'] : null;

    $params = [$from, $to];
    $userFilter = '';
    if ($user_id) { $userFilter = ' AND u.id = ?'; $params[] = $user_id; }

    $rows = q_all(
        "SELECT u.id, u.username, u.full_name, u.department, u.company, u.role,
                COUNT(t.id) AS sessions,
                COALESCE(SUM(t.bytes_down),0) AS d,
                COALESCE(SUM(t.bytes_up),0)   AS u_up,
                MAX(t.recorded_at) AS last_seen
         FROM users u
         JOIN traffic_usage t ON t.user_id = u.id
         WHERE date(t.recorded_at) BETWEEN ? AND ?$userFilter
         GROUP BY u.id
         ORDER BY (COALESCE(SUM(t.bytes_down),0) + COALESCE(SUM(t.bytes_up),0)) DESC",
        $params
    );

    $users = [];
    $tDown = 0; $tUp = 0;
    foreach ($rows as $r) {
        $down = (int)$r['d']; $up = (int)$r['u_up'];
        $tDown += $down; $tUp += $up;
        $users[] = [
            'user_id' => (int)$r['id'], 'username' => $r['username'], 'full_name' => $r['full_name'],
            'department' => $r['department'], 'company' => $r['company'], 'role' => $r['role'],
            'sessions' => (int)$r['sessions'],
            'bytes_down' => $down, 'bytes_up' => $up, 'bytes_total' => $down + $up,
            'down_fmt' => fmt_bytes($down), 'up_fmt' => fmt_bytes($up), 'total_fmt' => fmt_bytes($down + $up),
            'last_seen' => $r['last_seen'],
        ];
    }

    // Desglose diario (solo si se filtró un empleado)
    $daily = [];
    if ($user_id) {
        $drows = q_all(
            "SELECT date(recorded_at) AS day,
                    COALESCE(SUM(bytes_down),0) AS d, COALESCE(SUM(bytes_up),0) AS u_up
             FROM traffic_usage
             WHERE user_id = ? AND date(recorded_at) BETWEEN ? AND ?
             GROUP BY day ORDER BY day",
            [$user_id, $from, $to]
        );
        foreach ($drows as $r) {
            $down = (int)$r['d']; $up = (int)$r['u_up'];
            $daily[] = [
                'date' => $r['day'], 'bytes_down' => $down, 'bytes_up' => $up, 'bytes_total' => $down + $up,
                'down_fmt' => fmt_bytes($down), 'up_fmt' => fmt_bytes($up), 'total_fmt' => fmt_bytes($down + $up),
            ];
        }
    }

    json_out([
        'from' => $from, 'to' => $to, 'user_id' => $user_id,
        'users' => $users,
        'totals' => [
            'bytes_down' => $tDown, 'bytes_up' => $tUp, 'bytes_total' => $tDown + $tUp,
            'down_fmt' => fmt_bytes($tDown), 'up_fmt' => fmt_bytes($tUp), 'total_fmt' => fmt_bytes($tDown + $tUp),
        ],
        'daily' => $daily,
    ]);
}

function traffic_users() {
    require_admin();
    $rows = q_all(
        "SELECT u.id, u.username, u.full_name, u.role,
                COALESCE(SUM(t.bytes_down),0) AS total_down,
                COALESCE(SUM(t.bytes_up),0)   AS total_up,
                MAX(t.recorded_at) AS last_seen
         FROM users u
         LEFT JOIN traffic_usage t ON t.user_id = u.id
         WHERE u.approval_status = 'approved'
           AND EXISTS (SELECT 1 FROM devices d WHERE d.user_id = u.id)
         GROUP BY u.id
         ORDER BY (COALESCE(SUM(t.bytes_down),0) + COALESCE(SUM(t.bytes_up),0)) DESC"
    );
    $online = q_all("SELECT DISTINCT user_id FROM traffic_usage WHERE recorded_at >= datetime('now','-10 minutes')");
    $online_ids = array_map(fn($r) => (int)$r['user_id'], $online);

    $out = [];
    foreach ($rows as $r) {
        $down = (int)$r['total_down']; $up = (int)$r['total_up'];
        $out[] = [
            'user_id' => (int)$r['id'], 'username' => $r['username'], 'full_name' => $r['full_name'],
            'role' => $r['role'],
            'online' => in_array((int)$r['id'], $online_ids, true),
            'bytes_down' => $down, 'bytes_up' => $up, 'bytes_total' => $down + $up,
            'down_fmt' => fmt_bytes($down), 'up_fmt' => fmt_bytes($up),
            'total_fmt' => fmt_bytes($down + $up), 'last_seen' => $r['last_seen'],
        ];
    }
    json_out($out);
}
