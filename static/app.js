// ── State ──
let token = localStorage.getItem('token');
let currentUser = null;
let allUsers = [];
let allDevices = [];
let pendingApproveId = null;

const API = window.location.origin + '/api';

// ── Boot ──
document.addEventListener('DOMContentLoaded', () => {
    if (token) { showApp(); initApp(); }
    else showLogin();
});

// ── Auth ──
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUser').value.trim();
    const password = document.getElementById('loginPass').value;
    const btn = document.getElementById('loginBtn');
    const err = document.getElementById('loginError');
    err.classList.remove('show');

    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span> Ingresando…';

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            showApp();
            initApp();
        } else {
            const map = {
                'Invalid credentials':           'Usuario o contraseña incorrectos.',
                'User is inactive':              'Esta cuenta está inactiva.',
                'User account pending approval': 'Tu cuenta está pendiente de aprobación de un administrador.'
            };
            err.textContent = map[data.detail] || data.detail || 'Error al iniciar sesión.';
            err.classList.add('show');
        }
    } catch {
        err.textContent = 'Error de red. Verifica tu conexión.';
        err.classList.add('show');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Ingresar';
    }
}

function handleLogout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    showLogin();
    document.getElementById('loginForm').reset();
    document.getElementById('loginError').classList.remove('show');
}

// ── UI helpers ──
function showLogin() {
    document.getElementById('loginContainer').style.display = 'flex';
    document.getElementById('appContainer').style.display = 'none';
}
function showApp() {
    document.getElementById('loginContainer').style.display = 'none';
    document.getElementById('appContainer').style.display = 'flex';
}

function navigateTo(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const pageEl = document.getElementById(page + 'Page');
    if (pageEl) pageEl.classList.add('active');
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');

    if (page === 'dashboard')    loadDashboard();
    if (page === 'pendingUsers') loadPendingUsers();
    if (page === 'users')        loadUsers();
    if (page === 'devices')      loadDevices();
    if (page === 'messages')     { closeMsgDetail(); loadMessages(); }
    if (page === 'profile')      loadProfile();
    if (page === 'myAccess')     loadMyAccess();
    if (page === 'traffic')      loadTraffic();
}

function toast(msg, type = 'ok') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'show ' + type;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.className = ''; }, 3200);
}

function fmtDate(dt) {
    if (!dt) return '—';
    try { return new Date(dt).toLocaleDateString('es', { day:'2-digit', month:'short', year:'numeric' }); }
    catch { return dt; }
}
function fmtDateTime(dt) {
    if (!dt) return '—';
    try { return new Date(dt).toLocaleString('es', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }); }
    catch { return dt; }
}
function durationLabel(hours) {
    if (!hours) return null;
    if (hours < 24) return hours + ' horas';
    if (hours === 24) return '1 día';
    if (hours === 48) return '2 días';
    if (hours === 168) return '1 semana';
    return hours + ' h';
}

// ── Init (load profile + role-based nav) ──
async function initApp() {
    try {
        currentUser = await fetchAPI(`${API}/auth/me`);
        if (!currentUser) return handleLogout();

        document.getElementById('sidebarUser').textContent = currentUser.username;

        const isAdmin = currentUser.role === 'admin';

        // Mostrar/ocultar nav según rol
        document.querySelectorAll('.admin-nav').forEach(el => {
            el.style.display = isAdmin ? '' : 'none';
        });
        document.querySelectorAll('.user-nav').forEach(el => {
            el.style.display = isAdmin ? 'none' : 'flex';
        });

        updateMsgBadge();
        if (isAdmin) {
            refreshPendingBadge();
            navigateTo('dashboard');
        } else {
            navigateTo('myAccess');
        }
    } catch {
        handleLogout();
    }
}

async function refreshPendingBadge() {
    try {
        const list = await fetchAPI(`${API}/auth/pending-users`) || [];
        const badge = document.getElementById('pendingBadge');
        badge.textContent = list.length;
        badge.style.display = list.length > 0 ? 'inline-flex' : 'none';
    } catch { /* silent */ }
}

// ── Dashboard (admin) ──
async function loadDashboard() {
    try {
        const [users, devices] = await Promise.all([
            fetchAPI(`${API}/users/`).catch(() => []),
            fetchAPI(`${API}/devices/`).catch(() => [])
        ]);

        const uList = users || [];
        const dList = devices || [];
        document.getElementById('statTotal').textContent    = uList.length;
        document.getElementById('statPending').textContent  = uList.filter(u => u.approval_status === 'pending').length;
        document.getElementById('statApproved').textContent = uList.filter(u => u.approval_status === 'approved').length;
        document.getElementById('statDevices').textContent  = dList.length;

        document.getElementById('recentUsersTable').innerHTML = uList.slice(0, 6).map(u => `
            <tr>
                <td><strong>${escHtml(u.username)}</strong></td>
                <td>${escHtml(u.full_name)}</td>
                <td>${u.department || '—'}</td>
                <td>${statusBadge(u.approval_status)}</td>
                <td>${fmtDate(u.created_at)}</td>
            </tr>`).join('') || '<tr class="empty-row"><td colspan="5">Sin usuarios</td></tr>';
    } catch (e) { console.error(e); }
}

function refreshDashboard() { loadDashboard(); }

// ── Mi Acceso (usuario regular) ──
async function loadMyAccess() {
    const container = document.getElementById('myAccessContent');
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted)">Cargando…</div>';

    try {
        const [me, devices] = await Promise.all([
            fetchAPI(`${API}/auth/me`),
            fetchAPI(`${API}/auth/my-devices`).catch(() => [])
        ]);

        const status = me.approval_status || 'pending';
        const expires = me.access_expires_at;
        const now = new Date();
        const expDate = expires ? new Date(expires) : null;
        const isExpired = expDate && expDate < now;

        // Banner de estado
        const bannerCfg = {
            approved: { cls: 'approved', icon: '✅', title: '¡Acceso aprobado!',
                sub: 'Tu cuenta está activa y tienes acceso a la red WiFi.' },
            pending:  { cls: 'pending',  icon: '⏳', title: 'Solicitud en revisión',
                sub: 'Un administrador revisará tu solicitud pronto. Recibirás acceso cuando sea aprobada.' },
            rejected: { cls: 'rejected', icon: '🚫', title: 'Solicitud rechazada',
                sub: 'Tu solicitud no fue aprobada. Contacta al administrador para más información.' },
        };
        const cfg = bannerCfg[status] || bannerCfg.pending;

        let expiryHtml = '';
        if (status === 'approved' && expires) {
            if (isExpired) {
                expiryHtml = `<div class="access-expiry" style="background:rgba(220,38,38,.1);color:#991b1b">
                    ⚠️ Acceso expirado el ${fmtDateTime(expires)}
                </div>`;
            } else {
                expiryHtml = `<div class="access-expiry">
                    🕐 Válido hasta: ${fmtDateTime(expires)}
                </div>`;
            }
        } else if (status === 'approved' && !expires) {
            expiryHtml = `<div class="access-expiry">♾️ Acceso permanente</div>`;
        }

        // Info personal
        const infoRows = [
            ['Nombre',      me.full_name],
            ['Usuario',     me.username],
            ['Departamento',me.department || '—'],
            ['Cargo',       me.position   || '—'],
            ['Correo',      me.email      || '—'],
            ['Teléfono',    me.phone      || '—'],
            ['Registrado',  fmtDate(me.created_at)],
        ].filter(([, v]) => v && v !== '—').map(([l, v]) => `
            <div class="profile-field">
                <span class="profile-field-label">${l}</span>
                <span class="profile-field-val">${escHtml(String(v))}</span>
            </div>`).join('');

        // Dispositivos
        const devHtml = (devices || []).length === 0
            ? '<p style="color:var(--text-muted);font-size:.875rem">No hay dispositivos registrados.</p>'
            : `<div class="device-cards">${(devices || []).map(d => deviceCardHtml(d)).join('')}</div>`;

        container.innerHTML = `
            <div class="access-banner ${cfg.cls}">
                <div class="access-banner-icon">${cfg.icon}</div>
                <div>
                    <div class="access-banner-title">${cfg.title}</div>
                    <div class="access-banner-sub">${cfg.sub}</div>
                    ${expiryHtml}
                </div>
            </div>

            <div style="display:grid;gap:1.25rem;grid-template-columns:1fr 1fr;align-items:start">
                <div class="section-card">
                    <div class="section-card-header">👤 Mis datos</div>
                    <div style="padding:1.1rem 1.5rem">
                        <div class="profile-fields">${infoRows}</div>
                    </div>
                </div>
                <div class="section-card">
                    <div class="section-card-header">
                        📱 Mis dispositivos
                        <button class="btn btn-primary btn-sm" onclick="document.getElementById('addMyDeviceModal').classList.add('show')">+ Agregar</button>
                    </div>
                    <div style="padding:1.1rem 1.5rem">${devHtml}</div>
                </div>
            </div>`;
    } catch (e) {
        container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--danger)">Error al cargar.</div>';
    }
}

function deviceCardHtml(d) {
    const iconMap = { smartphone: '📱', tablet: '📟', laptop: '💻', desktop: '🖥️' };
    const icon = iconMap[(d.device_type || '').toLowerCase()] || '💻';
    return `<div class="device-card">
        <div class="device-card-header">
            <div class="device-card-icon">${icon}</div>
            <div>
                <div class="device-card-type">${d.device_type || 'Dispositivo'}</div>
                <div class="device-card-os">${[d.os_type, d.os_version].filter(Boolean).join(' ') || '—'}</div>
            </div>
        </div>
        ${d.mac_address ? `<div class="device-card-field">
            <span class="device-card-label">Dirección MAC</span>
            <span class="device-card-val">${d.mac_address}</span>
        </div>` : ''}
        ${d.ip_address ? `<div class="device-card-field">
            <span class="device-card-label">Dirección IP</span>
            <span class="device-card-val">${d.ip_address}</span>
        </div>` : ''}
        <div class="device-card-field">
            <span class="device-card-label">Registrado</span>
            <span class="device-card-val" style="font-family:inherit;font-size:.8rem">${fmtDate(d.registered_at)}</span>
        </div>
    </div>`;
}

// ── Pending users (cards) ──
async function loadPendingUsers() {
    const container = document.getElementById('pendingCards');
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted)">Cargando…</div>';

    try {
        const list = await fetchAPI(`${API}/auth/pending-users`) || [];
        if (list.length === 0) {
            container.innerHTML = `<div style="padding:3rem;text-align:center;color:var(--text-muted)">
                <div style="font-size:2.5rem;margin-bottom:.75rem">🎉</div>
                <strong>Sin solicitudes pendientes</strong>
                <p style="margin-top:.35rem;font-size:.875rem">Todas las solicitudes han sido procesadas.</p>
            </div>`;
            refreshPendingBadge();
            return;
        }
        container.innerHTML = '<div class="cards-grid">' + list.map(buildPendingCard).join('') + '</div>';
        refreshPendingBadge();
    } catch {
        container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--danger)">Error al cargar solicitudes.</div>';
    }
}

function buildPendingCard(u) {
    const isVisitor  = u.department === 'Visita / Externo';
    const ticketHtml = (isVisitor && u.ticket_number) ? `
        <div class="card-ticket">
            🎫 Ticket: <strong>${escHtml(u.ticket_number)}</strong>
            ${u.access_duration_hours ? `· ${durationLabel(u.access_duration_hours)}` : ''}
        </div>` : '';

    const deviceHtml = (u.mac_address || u.ip_address || u.device_type) ? `
        <div class="card-device">
            ${u.device_type ? `<div class="card-device-row">💻 <span>${escHtml(u.device_type)}${u.os_type ? ' · ' + escHtml(u.os_type) : ''}${u.os_version ? ' ' + escHtml(u.os_version) : ''}</span></div>` : ''}
            ${u.mac_address ? `<div class="card-device-row">🔑 <span style="font-family:monospace;font-size:.79rem">${escHtml(u.mac_address)}</span></div>` : ''}
            ${u.ip_address  ? `<div class="card-device-row">📍 <span>${escHtml(u.ip_address)}</span></div>` : ''}
        </div>` : '';

    return `
    <div class="pending-card" id="card-${u.id}">
        <div class="card-header-strip"></div>
        <div class="card-body">
            <div class="card-name">${escHtml(u.full_name)}</div>
            <div class="card-username">@${escHtml(u.username)}</div>
            <div class="card-meta">
                <div class="card-meta-item">
                    <span class="card-meta-label">Departamento</span>
                    <span class="card-meta-value">${u.department || '—'}</span>
                </div>
                <div class="card-meta-item">
                    <span class="card-meta-label">Cargo / Relación</span>
                    <span class="card-meta-value">${u.position || '—'}</span>
                </div>
                ${u.email ? `<div class="card-meta-item">
                    <span class="card-meta-label">Correo</span>
                    <span class="card-meta-value">${escHtml(u.email)}</span>
                </div>` : ''}
                ${u.phone ? `<div class="card-meta-item">
                    <span class="card-meta-label">Teléfono</span>
                    <span class="card-meta-value">${escHtml(u.phone)}</span>
                </div>` : ''}
            </div>
            ${ticketHtml}
            ${deviceHtml}
            <div class="card-date">📅 ${fmtDateTime(u.created_at)}</div>
        </div>
        <div class="card-footer">
            <button class="btn btn-danger btn-sm" onclick="rejectUser(${u.id})">✕ Rechazar</button>
            <button class="btn btn-success btn-sm" onclick="openApproveModal(${u.id},'${escAttr(u.full_name)}','${escAttr(u.department||'')}','${escAttr(u.position||'')}',${u.access_duration_hours||'null'})">
                ✓ Aprobar
            </button>
        </div>
    </div>`;
}

// ── Approve modal ──
function openApproveModal(id, name, dept, position, requestedHours) {
    pendingApproveId = id;
    document.getElementById('approveUserName').textContent = name;
    document.getElementById('approveUserMeta').textContent =
        [dept, position].filter(Boolean).join(' · ') || 'Sin información adicional';
    const sel = document.getElementById('approveHours');
    sel.value = requestedHours || '';
    document.getElementById('approveHint').textContent = requestedHours
        ? `El usuario solicitó ${durationLabel(requestedHours)}. Puedes modificarlo si lo deseas.`
        : 'Dejar en blanco para acceso permanente.';
    document.getElementById('approveModal').classList.add('show');
}

function closeApproveModal() {
    document.getElementById('approveModal').classList.remove('show');
    pendingApproveId = null;
}

async function confirmApprove() {
    if (!pendingApproveId) return;
    const btn = document.getElementById('approveConfirmBtn');
    const hours = document.getElementById('approveHours').value;
    const body = hours ? { access_hours: parseInt(hours, 10) } : {};
    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span> Aprobando…';
    try {
        await fetchAPI(`${API}/auth/approve-user/${pendingApproveId}`, { method: 'POST', body: JSON.stringify(body) });
        closeApproveModal();
        toast('✅ Usuario aprobado correctamente.', 'ok');
        loadPendingUsers();
    } catch {
        toast('❌ Error al aprobar. Intenta de nuevo.', 'err');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '✓ Confirmar aprobación';
    }
}

async function rejectUser(userId) {
    if (!confirm('¿Rechazar esta solicitud? El usuario no podrá acceder a la red.')) return;
    try {
        await fetchAPI(`${API}/auth/reject-user/${userId}`, { method: 'POST' });
        toast('Solicitud rechazada.', 'ok');
        loadPendingUsers();
    } catch {
        toast('❌ Error al rechazar.', 'err');
    }
}

// ── Users table (admin) ──
async function loadUsers() {
    try {
        allUsers = await fetchAPI(`${API}/users/`) || [];
        renderUsers(allUsers);
    } catch { /* silent */ }
}

function bwLabel(dl, ul) {
    if (!dl && !ul) return '<span style="color:var(--text-muted);font-size:.8rem">Sin límite</span>';
    const d = dl ? `⬇${dl}M` : '⬇∞';
    const u = ul ? `⬆${ul}M` : '⬆∞';
    return `<span style="font-size:.8rem;font-family:monospace;color:var(--primary)">${d} ${u}</span>`;
}

function renderUsers(list) {
    const isSuperadmin = currentUser?.username === 'admin';
    document.getElementById('usersTable').innerHTML = list.length === 0
        ? '<tr class="empty-row"><td colspan="9">Sin usuarios</td></tr>'
        : list.map(u => `
            <tr>
                <td><strong>${escHtml(u.username)}</strong></td>
                <td>${escHtml(u.full_name)}</td>
                <td>${u.department || '—'}</td>
                <td>${u.position || '—'}</td>
                <td>${u.email || '—'}</td>
                <td>${statusBadge(u.approval_status || '')}</td>
                <td>
                    ${bwLabel(u.download_mbps, u.upload_mbps)}
                    ${u.username !== 'admin' ? `<button class="btn btn-ghost btn-sm" style="margin-left:.4rem;padding:2px 7px" onclick="openBandwidthModal(${u.id},'${escAttr(u.full_name)}',${u.download_mbps||'null'},${u.upload_mbps||'null'})">✎</button>` : ''}
                </td>
                <td>${roleCell(u, isSuperadmin)}</td>
                <td style="white-space:nowrap">${accessActions(u)}</td>
            </tr>`).join('');
}

function accessActions(u) {
    if (u.username === 'admin') return '—';
    const s = u.approval_status;
    const btns = [];
    if (s === 'pending') {
        btns.push(`<button class="btn btn-success btn-sm" onclick="openApproveModal(${u.id},'${escAttr(u.full_name)}','${escAttr(u.department||'')}','${escAttr(u.position||'')}',${u.access_duration_hours||'null'})">✓ Aprobar</button>`);
        btns.push(`<button class="btn btn-danger  btn-sm" onclick="rejectUser(${u.id})">✕ Rechazar</button>`);
    } else if (s === 'approved') {
        btns.push(`<button class="btn btn-warning btn-sm" onclick="blockUser(${u.id},'${escAttr(u.full_name)}')">⊘ Bloquear</button>`);
        btns.push(`<button class="btn btn-ghost btn-sm" onclick="openBlocksModal(${u.id},'${escAttr(u.full_name)}')">🚫 Sitios</button>`);
    } else {
        btns.push(`<button class="btn btn-success btn-sm" onclick="reactivateUser(${u.id},'${escAttr(u.full_name)}')">↺ Reactivar</button>`);
    }
    return btns.join(' ');
}

// ── Ancho de banda ──────────────────────────────────────────────────────────
let _bwUserId = null;

function openBandwidthModal(userId, name, dl, ul) {
    _bwUserId = userId;
    document.getElementById('bwUserLabel').textContent = `Usuario: ${name}`;
    document.getElementById('bwDownload').value = dl ?? '';
    document.getElementById('bwUpload').value   = ul ?? '';
    document.getElementById('bandwidthModal').classList.add('show');
}

function closeBandwidthModal() {
    document.getElementById('bandwidthModal').classList.remove('show');
    _bwUserId = null;
}

async function saveBandwidth() {
    const dl = document.getElementById('bwDownload').value;
    const ul = document.getElementById('bwUpload').value;
    const body = {
        download_mbps: dl !== '' ? parseInt(dl, 10) : null,
        upload_mbps:   ul !== '' ? parseInt(ul, 10) : null,
    };
    try {
        await fetchAPI(`${API}/users/${_bwUserId}/bandwidth`, { method: 'PUT', body: JSON.stringify(body) });
        const msg = (body.download_mbps || body.upload_mbps)
            ? `Límite: ⬇${body.download_mbps ?? '∞'}M ⬆${body.upload_mbps ?? '∞'}M`
            : 'Sin límite de ancho de banda';
        toast(`Guardado. ${msg}. Aplicará en ~60s.`, 'ok');
        closeBandwidthModal();
        loadUsers();
    } catch (e) { toast(`Error: ${e.message}`, 'err'); }
}

async function blockUser(userId, name) {
    if (!confirm(`¿Bloquear acceso a "${name}"?\nPerderá el internet de inmediato.`)) return;
    try {
        await fetchAPI(`${API}/users/${userId}/access`, { method: 'PUT', body: JSON.stringify({ action: 'block' }) });
        toast(`⊘ Acceso bloqueado para ${name}.`, 'ok');
        loadUsers();
        loadDashboard();
    } catch { toast('❌ Error al bloquear.', 'err'); }
}

async function reactivateUser(userId, name) {
    if (!confirm(`¿Reactivar acceso a "${name}"?`)) return;
    try {
        await fetchAPI(`${API}/users/${userId}/access`, { method: 'PUT', body: JSON.stringify({ action: 'approve' }) });
        toast(`✅ Acceso reactivado para ${name}.`, 'ok');
        loadUsers();
        loadDashboard();
    } catch { toast('❌ Error al reactivar.', 'err'); }
}

function roleCell(u, isSuperadmin) {
    if (!isSuperadmin || u.username === 'admin') {
        return roleBadge(u.role);
    }
    return `<select class="role-select" onchange="updateUserRole(${u.id}, this.value)">
        <option value="user"  ${u.role === 'user'  ? 'selected' : ''}>Usuario</option>
        <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
    </select>`;
}

async function updateUserRole(userId, newRole) {
    try {
        await fetchAPI(`${API}/users/${userId}/role`, {
            method: 'PUT',
            body: JSON.stringify({ role: newRole })
        });
        toast(`✅ Rol actualizado a "${newRole === 'admin' ? 'Admin' : 'Usuario'}".`, 'ok');
        loadUsers();
    } catch (e) {
        toast('❌ Error al cambiar rol.', 'err');
        loadUsers(); // restore select state
    }
}

function filterUsers() {
    const q = document.getElementById('userSearch').value.toLowerCase();
    renderUsers(allUsers.filter(u =>
        u.username.toLowerCase().includes(q) ||
        u.full_name.toLowerCase().includes(q) ||
        (u.email && u.email.toLowerCase().includes(q)) ||
        (u.department && u.department.toLowerCase().includes(q))
    ));
}

// ── Devices table ──
async function loadDevices() {
    try {
        allDevices = await fetchAPI(`${API}/devices/`) || [];
        renderDevices(allDevices);
    } catch { /* silent */ }
}

function renderDevices(list) {
    document.getElementById('devicesTable').innerHTML = list.length === 0
        ? '<tr class="empty-row"><td colspan="7">Sin dispositivos</td></tr>'
        : list.map(d => `
            <tr>
                <td>
                    <strong>${escHtml(d.owner_name || d.owner_username || '—')}</strong>
                    ${d.owner_username ? `<br><small style="color:var(--text-muted)">${escHtml(d.owner_username)}</small>` : ''}
                </td>
                <td><code style="font-family:monospace;font-size:.82rem">${d.mac_address}</code></td>
                <td>${d.ip_address || '—'}</td>
                <td>${d.device_type || '—'}</td>
                <td>${[d.os_type, d.os_version].filter(Boolean).join(' ') || '—'}</td>
                <td>${fmtDate(d.created_at)}</td>
                <td>
                    <button class="btn btn-danger btn-sm"
                        onclick="deleteDevice(${d.id},'${escAttr(d.mac_address)}','${escAttr(d.owner_name||d.owner_username||'')}')">
                        🗑 Eliminar
                    </button>
                </td>
            </tr>`).join('');
}

async function deleteDevice(deviceId, mac, ownerName) {
    if (!confirm(`¿Eliminar el dispositivo ${mac}${ownerName ? ' de ' + ownerName : ''}?\nPerderá acceso a la red de inmediato.`)) return;
    try {
        await fetchAPI(`${API}/devices/${deviceId}`, { method: 'DELETE' });
        toast(`🗑 Dispositivo ${mac} eliminado.`, 'ok');
        loadDevices();
    } catch { toast('❌ Error al eliminar dispositivo.', 'err'); }
}

function filterDevices() {
    const q = document.getElementById('deviceSearch').value.toLowerCase();
    renderDevices(allDevices.filter(d =>
        d.mac_address.toLowerCase().includes(q) ||
        (d.hostname && d.hostname.toLowerCase().includes(q)) ||
        (d.ip_address && d.ip_address.toLowerCase().includes(q))
    ));
}

// ── Profile ──
async function loadProfile() {
    try {
        const u = await fetchAPI(`${API}/auth/me`);
        if (!u) return;

        const initials = u.full_name.split(' ').map(w => w[0]).slice(0,2).join('').toUpperCase();
        document.getElementById('profileAvatar').textContent = initials;
        document.getElementById('profileName').textContent = u.full_name;
        document.getElementById('profileRole').innerHTML = roleBadge(u.role);

        const fields = [
            ['Usuario',      u.username],
            ['Correo',       u.email      || '—'],
            ['Teléfono',     u.phone      || '—'],
            ['Departamento', u.department || '—'],
            ['Cargo',        u.position   || '—'],
            ['Rol',          u.role === 'admin' ? 'Administrador' : 'Usuario'],
            ['Estado',       u.approval_status === 'approved' ? 'Aprobado' :
                             u.approval_status === 'pending'  ? 'Pendiente' : 'Rechazado'],
            ['Registrado',   fmtDate(u.created_at)],
        ];

        document.getElementById('profileFields').innerHTML = fields.map(([label, val]) => `
            <div class="profile-field">
                <span class="profile-field-label">${label}</span>
                <span class="profile-field-val">${escHtml(String(val))}</span>
            </div>`).join('');

        // Reset change-password form
        ['pwCurrent','pwNew','pwConfirm'].forEach(id => { document.getElementById(id).value = ''; });
        document.getElementById('pwMsg').classList.remove('show');
        document.getElementById('pwOk').style.display = 'none';
    } catch { /* silent */ }
}

// ── Change password ──
async function changePassword() {
    const current = document.getElementById('pwCurrent').value;
    const newPw   = document.getElementById('pwNew').value;
    const confirm = document.getElementById('pwConfirm').value;
    const btn     = document.getElementById('pwBtn');
    const errEl   = document.getElementById('pwMsg');
    const okEl    = document.getElementById('pwOk');

    errEl.classList.remove('show');
    okEl.style.display = 'none';

    if (!current || !newPw || !confirm) {
        errEl.textContent = 'Completa todos los campos.';
        errEl.classList.add('show'); return;
    }
    if (newPw.length < 6) {
        errEl.textContent = 'La nueva contraseña debe tener al menos 6 caracteres.';
        errEl.classList.add('show'); return;
    }
    if (newPw !== confirm) {
        errEl.textContent = 'Las contraseñas no coinciden.';
        errEl.classList.add('show'); return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spin"></span> Actualizando…';

    try {
        const res = await fetch(`${API}/auth/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ current_password: current, new_password: newPw })
        });
        const data = await res.json();
        if (res.ok) {
            ['pwCurrent','pwNew','pwConfirm'].forEach(id => { document.getElementById(id).value = ''; });
            okEl.style.display = 'block';
            toast('✅ Contraseña actualizada.', 'ok');
        } else {
            const map = {
                'WRONG_PASSWORD':    'La contraseña actual es incorrecta.',
                'PASSWORD_TOO_SHORT':'La nueva contraseña debe tener al menos 6 caracteres.',
            };
            errEl.textContent = map[data.detail] || data.detail || 'Error al actualizar.';
            errEl.classList.add('show');
        }
    } catch {
        errEl.textContent = 'Error de red. Intenta de nuevo.';
        errEl.classList.add('show');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Actualizar contraseña';
    }
}

// ── Multi-dispositivo ────────────────────────────────────────────────────────

function formatMacInput(el) {
    let v = el.value.replace(/[^0-9a-fA-F]/g, '').toUpperCase();
    let out = '';
    for (let i = 0; i < v.length && i < 12; i++) {
        if (i > 0 && i % 2 === 0) out += ':';
        out += v[i];
    }
    el.value = out;
}

// Admin: abrir modal agregar dispositivo
async function openAddDeviceModal() {
    const sel = document.getElementById('addDevUser');
    sel.innerHTML = '<option value="">Selecciona un usuario…</option>';
    try {
        const users = await fetchAPI(`${API}/users/`) || [];
        users.filter(u => u.username !== 'admin').forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.full_name} (@${u.username}) — ${u.approval_status === 'approved' ? '✓ Aprobado' : u.approval_status}`;
            sel.appendChild(opt);
        });
    } catch { /* silent */ }
    document.getElementById('addDevMac').value = '';
    document.getElementById('addDevOs').value = '';
    document.getElementById('addDevType').value = 'unknown';
    document.getElementById('addDeviceModal').classList.add('show');
}

function closeAddDeviceModal() {
    document.getElementById('addDeviceModal').classList.remove('show');
}

async function submitAddDevice() {
    const userId   = document.getElementById('addDevUser').value;
    const mac      = document.getElementById('addDevMac').value.trim().toUpperCase();
    const devType  = document.getElementById('addDevType').value;
    const osText   = document.getElementById('addDevOs').value.trim();

    if (!userId) { toast('Selecciona un usuario.', 'err'); return; }
    if (mac.length !== 17) { toast('Ingresa una MAC válida (XX:XX:XX:XX:XX:XX).', 'err'); return; }

    try {
        await fetchAPI(`${API}/devices/`, {
            method: 'POST',
            body: JSON.stringify({
                user_id: parseInt(userId, 10),
                mac_address: mac,
                hostname: '',
                device_type: devType,
                os_type: osText || null,
            })
        });
        toast('✅ Dispositivo agregado.', 'ok');
        closeAddDeviceModal();
        loadDevices();
    } catch (e) {
        const msg = e?.message || '';
        if (msg.includes('409') || msg.includes('UNIQUE')) {
            toast('❌ Esa MAC ya está registrada.', 'err');
        } else {
            toast('❌ Error al agregar dispositivo.', 'err');
        }
    }
}

// Usuario: agregar su propio dispositivo desde "Mi acceso"
async function submitAddMyDevice() {
    const mac     = document.getElementById('addMyDevMac').value.trim().toUpperCase();
    const devType = document.getElementById('addMyDevType').value;

    if (mac.length !== 17) { toast('Ingresa una MAC válida (XX:XX:XX:XX:XX:XX).', 'err'); return; }

    try {
        await fetchAPI(`${API}/auth/add-device`, {
            method: 'POST',
            body: JSON.stringify({
                mac_address: mac,
                device_info: JSON.stringify({ type: devType })
            })
        });
        toast('✅ Dispositivo agregado. Conéctalo al WiFi para que obtenga acceso.', 'ok');
        document.getElementById('addMyDeviceModal').classList.remove('show');
        loadMyAccess();
    } catch (e) {
        const detail = String(e);
        const errMap = {
            'DEVICE_ALREADY_YOURS': 'Ese dispositivo ya está en tu cuenta.',
            'DEVICE_TAKEN':         'Esa MAC ya está registrada para otro usuario.',
            'MAC_RANDOMIZED':       'La MAC ingresada parece aleatoria. Usa la MAC física del dispositivo.',
        };
        const key = Object.keys(errMap).find(k => detail.includes(k));
        toast('❌ ' + (errMap[key] || 'Error al agregar dispositivo.'), 'err');
    }
}

// ── Messages / Consultas ──────────────────────────────────────────────────────
let allMessages = [];
let activeMsgId = null;

async function loadMessages() {
    try {
        allMessages = await fetchAPI(`${API}/messages/`) || [];
        renderMessages(allMessages);
        updateMsgBadge();
    } catch { /* silent */ }
}

async function updateMsgBadge() {
    try {
        const d = await fetchAPI(`${API}/messages/unread-count`);
        const n = d?.count || 0;
        const badge = document.getElementById('msgBadge');
        badge.textContent = n;
        badge.style.display = n > 0 ? '' : 'none';
    } catch { /* silent */ }
}

function renderMessages(list) {
    const isAdmin = currentUser?.role === 'admin';
    document.getElementById('msgsTable').innerHTML = list.length === 0
        ? '<tr class="empty-row"><td colspan="7">Sin consultas</td></tr>'
        : list.map(m => {
            const unread = !m.is_read;
            const fw = unread ? '700' : '400';
            const replied = m.reply_body ? '<span class="badge badge-approved" style="font-size:.7rem">Respondido</span>'
                                         : '<span class="badge badge-pending"  style="font-size:.7rem">Pendiente</span>';
            return `<tr style="cursor:pointer" onclick="openMsgDetail(${m.id})">
                <td>${unread ? '<span style="color:var(--primary);font-size:.85rem">●</span>' : ''}</td>
                <td style="font-weight:${fw}">${escHtml(m.from_user_name || m.from_username || '—')}</td>
                <td>${escHtml(m.to_user_name || 'Admin')}</td>
                <td style="font-weight:${fw}">${escHtml(m.subject)}</td>
                <td style="color:var(--text-muted);font-size:.8rem">${fmtDate(m.created_at)}</td>
                <td>${replied}</td>
                <td>
                    ${isAdmin ? `<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteMsg(${m.id})">🗑</button>` : ''}
                </td>
            </tr>`;
        }).join('');
}

async function openMsgDetail(msgId) {
    activeMsgId = msgId;
    const m = allMessages.find(x => x.id === msgId);
    if (!m) return;

    document.getElementById('msgListCard').style.display = 'none';
    document.getElementById('msgDetail').style.display = '';

    document.getElementById('msgDetailSubject').textContent = m.subject;
    document.getElementById('msgDetailDate').textContent = fmtDate(m.created_at);
    document.getElementById('msgDetailFrom').textContent = m.from_user_name || m.from_username || '—';
    const toWrap = document.getElementById('msgDetailToWrap');
    document.getElementById('msgDetailTo').textContent = m.to_user_name || 'Administración';
    toWrap.style.display = m.to_user_id || !m.from_user_id ? '' : 'none';
    document.getElementById('msgDetailBody').textContent = m.body;

    // Respuesta existente
    const replyDiv = document.getElementById('msgReplyExist');
    if (m.reply_body) {
        replyDiv.style.display = '';
        document.getElementById('msgReplyExistBody').textContent = m.reply_body;
        document.getElementById('msgReplyExistBy').textContent = m.replied_by_name || 'Admin';
        document.getElementById('msgReplyExistAt').textContent = fmtDate(m.reply_at);
        document.getElementById('msgReplyForm').style.display = 'none';
    } else {
        replyDiv.style.display = 'none';
        document.getElementById('msgReplyText').value = '';
        // Solo admins o el destinatario pueden responder
        const canReply = currentUser?.role === 'admin' || m.to_user_id === currentUser?.id;
        document.getElementById('msgReplyForm').style.display = canReply ? '' : 'none';
    }

    // Marcar como leído
    if (!m.is_read) {
        try {
            await fetchAPI(`${API}/messages/${msgId}/read`, { method: 'PUT' });
            m.is_read = true;
            updateMsgBadge();
        } catch { /* silent */ }
    }
}

function closeMsgDetail() {
    activeMsgId = null;
    document.getElementById('msgListCard').style.display = '';
    document.getElementById('msgDetail').style.display = 'none';
}

async function sendReply() {
    if (!activeMsgId) return;
    const text = document.getElementById('msgReplyText').value.trim();
    if (!text) { toast('Escribe una respuesta.', 'err'); return; }
    try {
        await fetchAPI(`${API}/messages/${activeMsgId}/reply`, {
            method: 'POST', body: JSON.stringify({ reply_body: text })
        });
        toast('✅ Respuesta enviada.', 'ok');
        await loadMessages();
        closeMsgDetail();
    } catch { toast('❌ Error al enviar respuesta.', 'err'); }
}

async function deleteMsg(msgId) {
    if (!confirm('¿Eliminar esta consulta?')) return;
    try {
        await fetchAPI(`${API}/messages/${msgId}`, { method: 'DELETE' });
        toast('🗑 Consulta eliminada.', 'ok');
        if (activeMsgId === msgId) closeMsgDetail();
        loadMessages();
    } catch { toast('❌ Error al eliminar.', 'err'); }
}

async function openNewMsgModal() {
    // Admin: cargar lista de usuarios para seleccionar destinatario
    const sel = document.getElementById('newMsgTo');
    sel.innerHTML = '<option value="">→ Administración (general)</option>';
    document.getElementById('newMsgToWrap').style.display = currentUser?.role === 'admin' ? '' : 'none';

    if (currentUser?.role === 'admin') {
        try {
            const users = await fetchAPI(`${API}/users/`) || [];
            users.filter(u => u.username !== 'admin').forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = `${u.full_name} (@${u.username})`;
                sel.appendChild(opt);
            });
        } catch { /* silent */ }
    }

    document.getElementById('newMsgSubject').value = '';
    document.getElementById('newMsgBody').value = '';
    document.getElementById('newMsgModal').classList.add('show');
}

function closeNewMsgModal() {
    document.getElementById('newMsgModal').classList.remove('show');
}

async function submitNewMsg() {
    const subject = document.getElementById('newMsgSubject').value.trim();
    const body    = document.getElementById('newMsgBody').value.trim();
    const toRaw   = document.getElementById('newMsgTo').value;
    const to_user_id = toRaw ? parseInt(toRaw, 10) : null;

    if (!subject || !body) { toast('Completa asunto y mensaje.', 'err'); return; }
    try {
        await fetchAPI(`${API}/messages/`, {
            method: 'POST', body: JSON.stringify({ subject, body, to_user_id })
        });
        toast('✅ Consulta enviada.', 'ok');
        closeNewMsgModal();
        loadMessages();
    } catch { toast('❌ Error al enviar consulta.', 'err'); }
}

// ── Utilities ──
function statusBadge(status) {
    const map = {
        pending:  ['badge-pending',  '⏳ Pendiente'],
        approved: ['badge-approved', '✓ Aprobado'],
        rejected: ['badge-rejected', '✕ Rechazado'],
    };
    const [cls, label] = map[status] || ['', status || '—'];
    return `<span class="badge ${cls}">${label}</span>`;
}

function roleBadge(role) {
    return role === 'admin'
        ? '<span class="badge badge-admin">Administrador</span>'
        : '<span class="badge badge-user">Usuario</span>';
}

function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(s) {
    return String(s).replace(/'/g,"\\'").replace(/"/g,'&quot;');
}

async function fetchAPI(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...(options.headers || {})
        }
    });
    if (res.status === 401) { handleLogout(); throw new Error('Unauthorized'); }
    if (!res.ok) {
        let detail = `HTTP_${res.status}`;
        try { const d = await res.json(); detail = d.detail || detail; } catch { /* */ }
        throw new Error(detail);
    }
    return res.json();
}

// Close approve modal on overlay click
document.addEventListener('click', e => {
    const overlay = document.getElementById('approveModal');
    if (e.target === overlay) closeApproveModal();
});

// ── CONSUMO DE ANCHO DE BANDA ─────────────────────────────────────────────────

function fmtBytes(b) {
    if (!b || b === 0) return '0 B';
    if (b >= 1073741824) return (b / 1073741824).toFixed(2) + ' GB';
    if (b >= 1048576)    return (b / 1048576).toFixed(2) + ' MB';
    if (b >= 1024)       return (b / 1024).toFixed(1) + ' KB';
    return b + ' B';
}

async function loadTraffic() {
    const tbody = document.getElementById('trafficTbody');
    const badge = document.getElementById('trafficOnlineBadge');
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted)">Cargando…</td></tr>';
    try {
        const data = await fetchAPI(`${API}/traffic/users`);
        if (!data.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted)">Sin datos aún — el router enviará estadísticas cada 5 min</td></tr>';
            return;
        }
        const online = data.filter(r => r.online).length;
        badge.textContent = `${online} en línea ahora`;
        tbody.innerHTML = data.map(r => `
            <tr>
                <td>
                    <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${r.online ? '#22c55e' : '#d1d5db'};margin-right:.4rem"></span>
                    ${r.online ? '<strong style="color:#16a34a">En línea</strong>' : '<span style="color:var(--text-muted)">Offline</span>'}
                </td>
                <td>
                    <div style="font-weight:600">${escHtml(r.full_name)}</div>
                    <div style="font-size:.78rem;color:var(--text-muted)">${escHtml(r.username)}</div>
                </td>
                <td style="font-size:.82rem;color:var(--text-muted)">${r.last_seen ? fmtDate(r.last_seen) : '—'}</td>
                <td style="text-align:right;color:#3b82f6;font-weight:500">${fmtBytes(r.bytes_down)}</td>
                <td style="text-align:right;color:#10b981;font-weight:500">${fmtBytes(r.bytes_up)}</td>
                <td style="text-align:right;font-weight:600">${fmtBytes(r.bytes_total)}</td>
            </tr>`).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:2rem;color:#ef4444">Error: ${escHtml(e.message)}</td></tr>`;
    }
}

// ── BLOQUEOS DE SITIOS POR USUARIO ───────────────────────────────────────────

let _blocksUserId = null;

function openBlocksModal(userId, name) {
    _blocksUserId = userId;
    document.getElementById('blocksUserLabel').textContent = `Usuario: ${name}`;
    document.getElementById('blockDomainInput').value = '';
    document.getElementById('blocksModal').classList.add('show');
    loadUserBlocks();
}

function closeBlocksModal() {
    document.getElementById('blocksModal').classList.remove('show');
    _blocksUserId = null;
}

async function loadUserBlocks() {
    const container = document.getElementById('blocksList');
    container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:1rem">Cargando…</div>';
    try {
        const data = await fetchAPI(`${API}/blocks/user/${_blocksUserId}`);
        if (!data.length) {
            container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:1rem;font-size:.88rem">Sin bloqueos configurados</div>';
            return;
        }
        container.innerHTML = data.map(b => `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:.45rem .65rem;background:#fef2f2;border:1px solid #fca5a5;border-radius:8px">
                <span style="font-family:monospace;font-size:.88rem;color:#991b1b">🚫 ${escHtml(b.domain)}</span>
                <button class="btn btn-ghost btn-sm" style="padding:2px 8px;color:#dc2626;border-color:#fca5a5" onclick="deleteBlock(${b.id})">✕</button>
            </div>`).join('');
    } catch (e) {
        container.innerHTML = `<div style="text-align:center;color:#ef4444;padding:1rem;font-size:.88rem">Error: ${escHtml(e.message)}</div>`;
    }
}

async function addBlock() {
    const input = document.getElementById('blockDomainInput');
    const domain = input.value.trim();
    if (!domain) return;
    try {
        const res = await fetchAPI(`${API}/blocks/user/${_blocksUserId}`, {
            method: 'POST',
            body: JSON.stringify({ domain }),
        });
        toast(res.message || 'Bloqueo agregado');
        input.value = '';
        await loadUserBlocks();
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    }
}

async function deleteBlock(blockId) {
    try {
        const res = await fetchAPI(`${API}/blocks/${blockId}`, { method: 'DELETE' });
        toast(res.message || 'Bloqueo eliminado');
        await loadUserBlocks();
    } catch (e) {
        toast(`Error: ${e.message}`, 'error');
    }
}

document.addEventListener('click', e => {
    if (e.target === document.getElementById('blocksModal')) closeBlocksModal();
});
