<?php
// /api/users/*  — port de app/routers/users.py

function _user_resp($u): array {
    return [
        'id' => (int)$u['id'], 'username' => $u['username'], 'full_name' => $u['full_name'],
        'email' => $u['email'], 'phone' => $u['phone'], 'department' => $u['department'],
        'position' => $u['position'], 'company' => $u['company'], 'role' => $u['role'],
        'is_active' => bool01($u['is_active']),
        'approval_status' => $u['approval_status'] ?? null,
        'created_at' => $u['created_at'] ?? null,
        'download_mbps' => isset($u['download_mbps']) && $u['download_mbps'] !== null ? (int)$u['download_mbps'] : null,
        'upload_mbps' => isset($u['upload_mbps']) && $u['upload_mbps'] !== null ? (int)$u['upload_mbps'] : null,
    ];
}

function _device_info($d): array {
    return [
        'id' => (int)$d['id'], 'mac_address' => $d['mac_address'], 'ip_address' => $d['ip_address'],
        'hostname' => $d['hostname'], 'device_type' => $d['device_type'] ?: 'unknown',
        'manufacturer' => $d['manufacturer'], 'model' => $d['model'], 'os_type' => $d['os_type'],
        'status' => $d['status'], 'last_seen' => $d['last_seen'],
    ];
}

function users_list() {
    require_auth();
    $rows = q_all("SELECT id, username, full_name, email, phone, department, position, company,
                          role, is_active, approval_status, created_at, download_mbps, upload_mbps
                   FROM users ORDER BY created_at DESC");
    json_out(array_map('_user_resp', $rows));
}

function users_create() {
    require_auth();
    $b = body_json();
    try {
        q("INSERT INTO users (username, password_hash, full_name, email, phone, department, position, company, role)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
           [$b['username'] ?? '', password_hash($b['password'] ?? '', PASSWORD_BCRYPT),
            $b['full_name'] ?? '', $b['email'] ?? null, $b['phone'] ?? null,
            $b['department'] ?? null, $b['position'] ?? null, $b['company'] ?? null, $b['role'] ?? 'user']);
        $id = last_id();
    } catch (Throwable $e) {
        abort(400, 'User creation failed: ' . $e->getMessage());
    }
    $u = q_one("SELECT * FROM users WHERE id = ?", [$id]);
    json_out(_user_resp($u));
}

function users_detail($user_id) {
    require_auth();
    $u = q_one("SELECT id, username, full_name, email, phone, department, position, company, role, is_active, created_at, last_login
                FROM users WHERE id = ?", [$user_id]);
    if (!$u) abort(404, 'User not found');
    $devs = q_all("SELECT id, mac_address, ip_address, hostname, device_type, manufacturer, model, os_type, status, last_seen
                   FROM devices WHERE user_id = ? ORDER BY created_at DESC", [$user_id]);
    $dl = array_map('_device_info', $devs);
    $resp = _user_resp($u + ['company' => $u['company'] ?? null, 'approval_status' => null, 'download_mbps' => null, 'upload_mbps' => null]);
    $resp['devices'] = $dl;
    $resp['device_count'] = count($dl);
    $resp['last_login'] = $u['last_login'];
    json_out($resp);
}

function users_update($user_id) {
    require_auth();
    if (!q_one("SELECT id FROM users WHERE id = ?", [$user_id])) abort(404, 'User not found');
    $b = body_json();
    $sets = []; $vals = [];
    foreach (['full_name','email','phone','department','position','company','role'] as $f) {
        if (array_key_exists($f, $b) && $b[$f] !== null) { $sets[] = "$f = ?"; $vals[] = $b[$f]; }
    }
    if ($sets) {
        $sets[] = "updated_at = CURRENT_TIMESTAMP";
        $vals[] = $user_id;
        q("UPDATE users SET " . implode(', ', $sets) . " WHERE id = ?", $vals);
    }
    $u = q_one("SELECT * FROM users WHERE id = ?", [$user_id]);
    json_out(_user_resp($u));
}

function users_delete($user_id) {
    require_auth();
    q("DELETE FROM users WHERE id = ?", [$user_id]);
    json_out(['message' => 'User deleted successfully']);
}

function users_set_access($user_id) {
    require_admin();
    $b = body_json();
    $action = $b['action'] ?? '';
    if (!in_array($action, ['approve','block','reject'], true)) abort(400, "Acción inválida. Usa 'approve', 'block' o 'reject'.");
    $t = q_one("SELECT id, username FROM users WHERE id = ?", [$user_id]);
    if (!$t) abort(404, 'Usuario no encontrado.');
    if ($t['username'] === 'admin') abort(400, 'No se puede modificar el administrador principal.');
    if ($action === 'approve') { $st = 'approved'; $active = 1; } else { $st = 'rejected'; $active = 0; }
    q("UPDATE users SET approval_status = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", [$st, $active, $user_id]);
    json_out(['message' => 'Acceso actualizado', 'approval_status' => $st, 'is_active' => (bool)$active]);
}

function users_set_bandwidth($user_id) {
    require_admin();
    $b = body_json();
    $dl = array_key_exists('download_mbps', $b) ? $b['download_mbps'] : null;
    $ul = array_key_exists('upload_mbps', $b) ? $b['upload_mbps'] : null;
    if (!q_one("SELECT id FROM users WHERE id = ?", [$user_id])) abort(404, 'Usuario no encontrado.');
    if ($dl !== null && (int)$dl < 0) abort(400, 'El límite de descarga no puede ser negativo.');
    if ($ul !== null && (int)$ul < 0) abort(400, 'El límite de subida no puede ser negativo.');
    q("UPDATE users SET download_mbps = ?, upload_mbps = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
      [$dl !== null ? (int)$dl : null, $ul !== null ? (int)$ul : null, $user_id]);
    json_out(['ok' => true, 'download_mbps' => $dl, 'upload_mbps' => $ul]);
}

function users_set_role($user_id) {
    $u = require_admin();
    $b = body_json();
    $role = $b['role'] ?? '';
    if (!in_array($role, ['user','admin'], true)) abort(400, "Rol inválido. Usa 'user' o 'admin'.");
    if ($u['username'] !== 'admin') abort(403, 'Solo el administrador principal puede cambiar roles.');
    $t = q_one("SELECT username FROM users WHERE id = ?", [$user_id]);
    if (!$t) abort(404, 'Usuario no encontrado.');
    if ($t['username'] === 'admin') abort(400, 'No se puede cambiar el rol del administrador principal.');
    q("UPDATE users SET role = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", [$role, $user_id]);
    json_out(['message' => 'Rol actualizado', 'role' => $role]);
}

function users_devices($user_id) {
    require_auth();
    if (!q_one("SELECT id FROM users WHERE id = ?", [$user_id])) abort(404, 'User not found');
    $devs = q_all("SELECT id, mac_address, ip_address, hostname, device_type, manufacturer, model, os_type, status, last_seen
                   FROM devices WHERE user_id = ? ORDER BY created_at DESC", [$user_id]);
    json_out(array_map('_device_info', $devs));
}
