<?php
// /api/messages/*  — port de app/routers/messages.py

const MSG_SELECT = "
    SELECT m.id, m.from_user_id, fu.full_name AS from_name, fu.username AS from_username,
           m.to_user_id, tu.full_name AS to_name, m.subject, m.body, m.is_read,
           m.reply_body, m.reply_at, rb.full_name AS replied_by_name, m.created_at
    FROM messages m
    LEFT JOIN users fu ON m.from_user_id = fu.id
    LEFT JOIN users tu ON m.to_user_id = tu.id
    LEFT JOIN users rb ON m.replied_by = rb.id";

function _msg_out($r): array {
    return [
        'id' => (int)$r['id'], 'from_user_id' => (int)$r['from_user_id'],
        'from_user_name' => $r['from_name'], 'from_username' => $r['from_username'],
        'to_user_id' => $r['to_user_id'] !== null ? (int)$r['to_user_id'] : null,
        'to_user_name' => $r['to_name'], 'subject' => $r['subject'], 'body' => $r['body'],
        'is_read' => bool01($r['is_read']), 'reply_body' => $r['reply_body'],
        'reply_at' => $r['reply_at'], 'replied_by_name' => $r['replied_by_name'],
        'created_at' => (string)$r['created_at'],
    ];
}

function _msg_caller() {
    $p = require_auth();
    $u = q_one("SELECT id, full_name, role FROM users WHERE username = ?", [$p['sub']]);
    if (!$u) abort(404, 'Usuario no encontrado');
    return $u;
}

function messages_send() {
    $c = _msg_caller();
    $b = body_json();
    $to = ($c['role'] === 'admin') ? ($b['to_user_id'] ?? null) : null;
    q("INSERT INTO messages (from_user_id, to_user_id, subject, body) VALUES (?, ?, ?, ?)",
      [$c['id'], $to, trim($b['subject'] ?? ''), trim($b['body'] ?? '')]);
    $id = last_id();
    json_out(_msg_out(q_one(MSG_SELECT . " WHERE m.id = ?", [$id])));
}

function messages_list() {
    $c = _msg_caller();
    if ($c['role'] === 'admin') {
        $rows = q_all(MSG_SELECT . " ORDER BY m.created_at DESC");
    } else {
        $rows = q_all(MSG_SELECT . " WHERE m.from_user_id = ? OR m.to_user_id = ? ORDER BY m.created_at DESC",
                      [$c['id'], $c['id']]);
    }
    json_out(array_map('_msg_out', $rows));
}

function messages_unread_count() {
    $c = _msg_caller();
    if ($c['role'] === 'admin') {
        $row = q_one("SELECT COUNT(*) AS n FROM messages WHERE (to_user_id IS NULL OR to_user_id = ?) AND is_read = 0 AND from_user_id != ?",
                     [$c['id'], $c['id']]);
    } else {
        $row = q_one("SELECT COUNT(*) AS n FROM messages WHERE to_user_id = ? AND is_read = 0", [$c['id']]);
    }
    json_out(['count' => $row ? (int)$row['n'] : 0]);
}

function messages_mark_read($id) {
    $c = _msg_caller();
    q("UPDATE messages SET is_read = 1 WHERE id = ? AND (to_user_id = ? OR (to_user_id IS NULL AND ? = 'admin'))",
      [$id, $c['id'], $c['role']]);
    json_out(['ok' => true]);
}

function messages_reply($id) {
    $c = _msg_caller();
    $b = body_json();
    $msg = q_one("SELECT id, to_user_id FROM messages WHERE id = ?", [$id]);
    if (!$msg) abort(404, 'Mensaje no encontrado');
    if ($c['role'] !== 'admin' && (int)$msg['to_user_id'] !== (int)$c['id']) abort(403, 'Sin permiso para responder');
    q("UPDATE messages SET reply_body = ?, reply_at = CURRENT_TIMESTAMP, replied_by = ?, is_read = 1 WHERE id = ?",
      [trim($b['reply_body'] ?? ''), $c['id'], $id]);
    json_out(_msg_out(q_one(MSG_SELECT . " WHERE m.id = ?", [$id])));
}

function messages_delete($id) {
    $c = _msg_caller();
    if ($c['role'] !== 'admin') abort(403, 'Solo administradores');
    q("DELETE FROM messages WHERE id = ?", [$id]);
    json_out(['ok' => true]);
}
