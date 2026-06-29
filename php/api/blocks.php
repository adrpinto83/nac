<?php
// /api/blocks/*  — port de app/routers/blocks.py
// El bloqueo se aplica en el router vía pull-script (DNS estático), no por llamada directa.

function _clean_domain(string $domain): string {
    $d = strtolower(trim($domain));
    foreach (['https://', 'http://', 'www.'] as $pre) {
        if (strpos($d, $pre) === 0) $d = substr($d, strlen($pre));
    }
    $d = explode('?', explode('/', $d)[0])[0];
    return $d;
}

function blocks_list_user($user_id) {
    require_admin();
    $rows = q_all("SELECT id, domain, created_at FROM user_site_blocks WHERE user_id = ? ORDER BY created_at DESC", [$user_id]);
    $out = [];
    foreach ($rows as $r) $out[] = ['id' => (int)$r['id'], 'domain' => $r['domain'], 'created_at' => $r['created_at']];
    json_out($out);
}

function blocks_add_user($user_id) {
    $admin = require_admin();
    $b = body_json();
    $domain = _clean_domain($b['domain'] ?? '');
    if (!$domain || strpos($domain, '.') === false) abort(400, 'Dominio inválido');
    if (!q_one("SELECT id FROM users WHERE id = ?", [$user_id])) abort(404, 'Usuario no encontrado');
    try {
        q("INSERT INTO user_site_blocks (user_id, domain, created_by) VALUES (?, ?, ?)",
          [$user_id, $domain, $admin['id']]);
        $id = last_id();
    } catch (Throwable $e) {
        abort(400, 'El dominio ya está bloqueado para este usuario');
    }
    json_out(['id' => $id, 'domain' => $domain,
              'message' => 'Bloqueo agregado. Se aplicará en el router en el próximo sync (≤60s).']);
}

function blocks_remove($block_id) {
    require_admin();
    $row = q_one("SELECT id, user_id, domain FROM user_site_blocks WHERE id = ?", [$block_id]);
    if (!$row) abort(404, 'Bloqueo no encontrado');
    q("DELETE FROM user_site_blocks WHERE id = ?", [$block_id]);
    json_out(['message' => 'Bloqueo eliminado. Se quitará del router en el próximo sync (≤60s).']);
}
