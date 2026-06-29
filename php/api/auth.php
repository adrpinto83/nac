<?php
// /api/auth/*  — port de app/routers/auth.py

function auth_login() {
    $b = body_json();
    $username = $b['username'] ?? '';
    $password = $b['password'] ?? '';
    $u = q_one("SELECT id, username, password_hash, role, is_active, approval_status FROM users WHERE username = ?", [$username]);
    if (!$u || !password_verify($password, $u['password_hash'])) abort(401, 'Invalid credentials');
    if (!bool01($u['is_active'])) abort(401, 'User is inactive');
    if ($u['approval_status'] !== 'approved') abort(401, 'User account pending approval');
    $token = create_access_token(['sub' => $u['username']]);
    json_out(['access_token' => $token, 'token_type' => 'bearer']);
}

function auth_me() {
    $p = require_auth();
    $u = q_one("SELECT id, username, full_name, email, phone, department, position, role,
                       is_active, approval_status, access_expires_at, created_at
                FROM users WHERE username = ?", [$p['sub']]);
    if (!$u) abort(404, 'User not found');
    json_out([
        'id' => (int)$u['id'], 'username' => $u['username'], 'full_name' => $u['full_name'],
        'email' => $u['email'], 'phone' => $u['phone'], 'department' => $u['department'],
        'position' => $u['position'], 'role' => $u['role'], 'is_active' => bool01($u['is_active']),
        'approval_status' => $u['approval_status'],
        'access_expires_at' => $u['access_expires_at'] ? (string)$u['access_expires_at'] : null,
        'created_at' => $u['created_at'] ? (string)$u['created_at'] : null,
    ]);
}

function auth_logout() { json_out(['message' => 'Logged out successfully']); }

function auth_change_password() {
    $p = require_auth();
    $b = body_json();
    $new = $b['new_password'] ?? '';
    $cur = $b['current_password'] ?? '';
    if (strlen($new) < 6) abort(400, 'PASSWORD_TOO_SHORT');
    $u = q_one("SELECT id, password_hash FROM users WHERE username = ?", [$p['sub']]);
    if (!$u) abort(404, 'User not found');
    if (!password_verify($cur, $u['password_hash'])) abort(400, 'WRONG_PASSWORD');
    q("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [password_hash($new, PASSWORD_BCRYPT), $u['id']]);
    json_out(['message' => 'Contraseña actualizada']);
}

function auth_my_devices() {
    $p = require_auth();
    $u = q_one("SELECT id FROM users WHERE username = ?", [$p['sub']]);
    if (!$u) abort(404, 'User not found');
    $rows = q_all("SELECT mac_address, ip_address, device_type, os_type, os_version, created_at
                   FROM devices WHERE user_id = ? ORDER BY created_at DESC", [$u['id']]);
    $out = [];
    foreach ($rows as $d) {
        $out[] = ['mac_address' => $d['mac_address'], 'ip_address' => $d['ip_address'],
                  'device_type' => $d['device_type'], 'os_type' => $d['os_type'],
                  'os_version' => $d['os_version'], 'registered_at' => $d['created_at']];
    }
    json_out($out);
}

function auth_registration_status() {
    $mac = $_GET['mac'] ?? '';
    if (!$mac) json_out(['status' => 'not_registered']);
    $row = q_one("SELECT u.approval_status AS us, COALESCE(d.approval_status,'approved') AS ds
                  FROM users u JOIN devices d ON d.user_id = u.id
                  WHERE d.mac_address = ? LIMIT 1", [$mac]);
    if (!$row) json_out(['status' => 'not_registered']);
    if ($row['us'] === 'rejected') json_out(['status' => 'rejected']);
    if ($row['us'] === 'pending' || $row['ds'] === 'pending') json_out(['status' => 'pending']);
    json_out(['status' => 'approved']);
}

function auth_register() {
    $b = body_json();
    $mac = $b['mac_address'] ?? null;
    $username = $b['username'] ?? '';

    if ($mac && is_random_mac($mac)) abort(400, 'MAC_RANDOMIZED');

    if ($mac) {
        $row = q_one("SELECT u.approval_status AS s FROM devices d JOIN users u ON u.id = d.user_id
                      WHERE d.mac_address = ? LIMIT 1", [$mac]);
        if ($row) abort(409, 'ALREADY_REGISTERED:' . $row['s']);
    }

    $dev = json_decode($b['device_info'] ?? '{}', true) ?: [];

    $existing = q_one("SELECT id, approval_status FROM users WHERE username = ?", [$username]);
    if ($existing) {
        if ($mac) {
            q("INSERT OR IGNORE INTO devices
                (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [$existing['id'], $mac, $b['ip_address'] ?? null, $b['full_name'] ?? '',
                 $dev['type'] ?? 'unknown', $dev['os'] ?? '', $dev['os_version'] ?? '', $b['device_info'] ?? null]);
        }
        abort(409, 'ALREADY_REGISTERED:' . $existing['approval_status']);
    }

    $hash = password_hash($b['password'] ?? '', PASSWORD_BCRYPT);
    q("INSERT INTO users
        (username, full_name, email, phone, department, position, company,
         ticket_number, access_duration_hours, password_hash, role, is_active, approval_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [$username, $b['full_name'] ?? '', $b['email'] ?? null, $b['phone'] ?? null,
         $b['department'] ?? null, $b['position'] ?? null, $b['company'] ?? null,
         $b['ticket_number'] ?? null, $b['access_duration_hours'] ?? null,
         $hash, 'user', 0, 'pending']);
    $uid = last_id();

    if ($mac) {
        q("INSERT OR IGNORE INTO devices
            (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [$uid, $mac, $b['ip_address'] ?? null, $b['full_name'] ?? '',
             $dev['type'] ?? 'unknown', $dev['os'] ?? '', $dev['os_version'] ?? '', $b['device_info'] ?? null]);
    }

    json_out(['id' => $uid, 'username' => $username, 'full_name' => $b['full_name'] ?? '',
              'email' => $b['email'] ?? null, 'role' => 'user', 'is_active' => false]);
}

function auth_pending_users() {
    require_admin();
    $rows = q_all("SELECT u.id, u.username, u.full_name, u.email, u.phone, u.department, u.position,
                          u.ticket_number, u.access_duration_hours, u.approval_status, u.created_at,
                          d.mac_address, d.ip_address, d.device_type, d.os_type, d.os_version
                   FROM users u LEFT JOIN devices d ON d.user_id = u.id
                   WHERE u.approval_status = 'pending'
                   ORDER BY u.created_at DESC");
    $out = [];
    foreach ($rows as $p) {
        $out[] = [
            'id' => (int)$p['id'], 'username' => $p['username'], 'full_name' => $p['full_name'],
            'email' => $p['email'], 'phone' => $p['phone'], 'department' => $p['department'],
            'position' => $p['position'], 'ticket_number' => $p['ticket_number'],
            'access_duration_hours' => $p['access_duration_hours'] !== null ? (int)$p['access_duration_hours'] : null,
            'approval_status' => $p['approval_status'], 'created_at' => (string)$p['created_at'],
            'mac_address' => $p['mac_address'], 'ip_address' => $p['ip_address'],
            'device_type' => $p['device_type'], 'os_type' => $p['os_type'], 'os_version' => $p['os_version'],
        ];
    }
    json_out($out);
}

function auth_approve_user($user_id) {
    require_admin();
    $b = body_json();
    $hours = $b['access_hours'] ?? null;
    $expires = null;
    if ($hours) $expires = gmdate('Y-m-d\TH:i:s.000000', time() + ((int)$hours * 3600));
    q("UPDATE users SET approval_status='approved', is_active=1, access_expires_at=? WHERE id=?", [$expires, $user_id]);
    q("UPDATE devices SET approval_status='approved' WHERE user_id=?", [$user_id]);
    json_out(['message' => 'User approved', 'expires_at' => $expires]);
}

function auth_reject_user($user_id) {
    require_admin();
    q("UPDATE users SET approval_status='rejected' WHERE id=?", [$user_id]);
    json_out(['message' => 'User rejected']);
}

function auth_add_device() {
    $p = require_auth();
    $b = body_json();
    $mac = strtoupper(trim($b['mac_address'] ?? ''));
    if (is_random_mac($mac)) abort(400, 'MAC_RANDOMIZED');
    $u = q_one("SELECT id, approval_status FROM users WHERE username = ?", [$p['sub']]);
    if (!$u) abort(404, 'Usuario no encontrado');
    $existing = q_one("SELECT user_id FROM devices WHERE mac_address = ?", [$mac]);
    if ($existing) {
        if ((int)$existing['user_id'] === (int)$u['id']) abort(409, 'DEVICE_ALREADY_YOURS');
        abort(409, 'DEVICE_TAKEN');
    }
    $dev = json_decode($b['device_info'] ?? '{}', true) ?: [];
    q("INSERT INTO devices
        (user_id, mac_address, ip_address, hostname, device_type, os_type, os_version, notes, approval_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
        [$u['id'], $mac, $b['ip_address'] ?? null, $dev['hostname'] ?? '',
         $dev['type'] ?? 'unknown', $dev['os'] ?? '', $dev['os_version'] ?? '', $b['device_info'] ?? null]);
    json_out(['ok' => true, 'mac_address' => $mac, 'approval_status' => 'pending',
              'message' => 'Dispositivo agregado. Pendiente de aprobación del administrador.']);
}
