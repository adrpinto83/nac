<?php
// /api/devices/*  — port de app/routers/devices.py

function _device_resp($d): array {
    return [
        'id' => (int)$d['id'], 'user_id' => (int)$d['user_id'], 'mac_address' => $d['mac_address'],
        'ip_address' => $d['ip_address'], 'hostname' => $d['hostname'],
        'device_type' => $d['device_type'] ?: 'unknown', 'manufacturer' => $d['manufacturer'],
        'model' => $d['model'], 'serial_number' => $d['serial_number'], 'os_type' => $d['os_type'],
        'os_version' => $d['os_version'], 'status' => $d['status'], 'last_seen' => $d['last_seen'],
        'notes' => $d['notes'], 'created_at' => $d['created_at'],
        'approval_status' => $d['approval_status'] ?? 'pending',
        'owner_name' => $d['owner_name'] ?? null, 'owner_username' => $d['owner_username'] ?? null,
    ];
}

function devices_list() {
    require_auth();
    $rows = q_all("SELECT d.*, u.full_name AS owner_name, u.username AS owner_username
                   FROM devices d LEFT JOIN users u ON d.user_id = u.id
                   ORDER BY d.created_at DESC");
    json_out(array_map('_device_resp', $rows));
}

function devices_create() {
    require_auth();
    $b = body_json();
    if (!q_one("SELECT id FROM users WHERE id = ?", [$b['user_id'] ?? 0])) abort(404, 'User not found');
    try {
        q("INSERT INTO devices (user_id, mac_address, hostname, device_type, manufacturer, model, serial_number, os_type, os_version, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
           [$b['user_id'], $b['mac_address'] ?? '', $b['hostname'] ?? '', $b['device_type'] ?? 'unknown',
            $b['manufacturer'] ?? null, $b['model'] ?? null, $b['serial_number'] ?? null,
            $b['os_type'] ?? null, $b['os_version'] ?? null, 'online', $b['notes'] ?? null]);
        $id = last_id();
    } catch (Throwable $e) {
        abort(400, 'Device registration failed: ' . $e->getMessage());
    }
    json_out(_device_resp(q_one("SELECT d.*, u.full_name AS owner_name, u.username AS owner_username
                                 FROM devices d LEFT JOIN users u ON d.user_id = u.id WHERE d.id = ?", [$id])));
}

function devices_get($id) {
    require_auth();
    $d = q_one("SELECT * FROM devices WHERE id = ?", [$id]);
    if (!$d) abort(404, 'Device not found');
    json_out(_device_resp($d));
}

function devices_update($id) {
    require_auth();
    if (!q_one("SELECT id FROM devices WHERE id = ?", [$id])) abort(404, 'Device not found');
    $b = body_json();
    $sets = []; $vals = [];
    if (array_key_exists('user_id', $b) && $b['user_id']) {
        if (!q_one("SELECT id FROM users WHERE id = ?", [$b['user_id']])) abort(404, 'User not found');
        $sets[] = "user_id = ?"; $vals[] = (int)$b['user_id'];
    }
    foreach (['hostname','device_type','manufacturer','model','serial_number','os_type','os_version','status','notes'] as $f) {
        if (array_key_exists($f, $b) && $b[$f] !== null) { $sets[] = "$f = ?"; $vals[] = $b[$f]; }
    }
    if ($sets) {
        $sets[] = "updated_at = CURRENT_TIMESTAMP"; $vals[] = $id;
        q("UPDATE devices SET " . implode(', ', $sets) . " WHERE id = ?", $vals);
    }
    json_out(_device_resp(q_one("SELECT d.*, u.full_name AS owner_name, u.username AS owner_username
                                 FROM devices d LEFT JOIN users u ON d.user_id = u.id WHERE d.id = ?", [$id])));
}

function devices_approve($id) {
    require_admin();
    $d = q_one("SELECT id, mac_address FROM devices WHERE id = ?", [$id]);
    if (!$d) abort(404, 'Dispositivo no encontrado');
    q("UPDATE devices SET approval_status='approved' WHERE id = ?", [$id]);
    json_out(['ok' => true, 'device_id' => (int)$id, 'mac_address' => $d['mac_address'], 'approval_status' => 'approved']);
}

function devices_reject($id) {
    require_admin();
    q("UPDATE devices SET approval_status='rejected' WHERE id = ?", [$id]);
    json_out(['ok' => true, 'device_id' => (int)$id, 'approval_status' => 'rejected']);
}

function devices_pending_list() {
    require_admin();
    $rows = q_all("SELECT d.id, d.mac_address, d.ip_address, d.device_type, d.os_type, d.os_version,
                          d.created_at, u.full_name, u.username, u.department
                   FROM devices d JOIN users u ON d.user_id = u.id
                   WHERE d.approval_status = 'pending' ORDER BY d.created_at DESC");
    $out = [];
    foreach ($rows as $r) {
        $out[] = ['id' => (int)$r['id'], 'mac_address' => $r['mac_address'], 'ip_address' => $r['ip_address'],
                  'device_type' => $r['device_type'], 'os_type' => $r['os_type'], 'os_version' => $r['os_version'],
                  'created_at' => $r['created_at'], 'owner_name' => $r['full_name'],
                  'owner_username' => $r['username'], 'department' => $r['department']];
    }
    json_out($out);
}

function devices_delete($id) {
    require_auth();
    q("DELETE FROM devices WHERE id = ?", [$id]);
    json_out(['message' => 'Device deleted successfully']);
}

function devices_by_user($user_id) {
    require_auth();
    if (!q_one("SELECT id FROM users WHERE id = ?", [$user_id])) abort(404, 'User not found');
    $rows = q_all("SELECT * FROM devices WHERE user_id = ? ORDER BY created_at DESC", [$user_id]);
    json_out(array_map('_device_resp', $rows));
}

function devices_by_mac($mac) {
    require_auth();
    $d = q_one("SELECT * FROM devices WHERE mac_address = ?", [$mac]);
    if (!$d) abort(404, 'Device not found');
    json_out(_device_resp($d));
}
