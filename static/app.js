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
                'Invalid credentials':          'Usuario o contraseña incorrectos.',
                'User is inactive':             'Esta cuenta está inactiva.',
                'User account pending approval':'Tu cuenta está pendiente de aprobación.'
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
    document.getElementById(page + 'Page').classList.add('active');
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (navEl) navEl.classList.add('active');

    if (page === 'dashboard')    loadDashboard();
    if (page === 'pendingUsers') loadPendingUsers();
    if (page === 'users')        loadUsers();
    if (page === 'devices')      loadDevices();
    if (page === 'profile')      loadProfile();
}

function toast(msg, type = 'ok') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = 'show ' + type;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.className = ''; }, 3000);
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
    return hours + ' horas';
}

// ── Init (load profile + badges) ──
async function initApp() {
    try {
        currentUser = await fetchAPI(`${API}/auth/me`);
        if (!currentUser) return handleLogout();

        document.getElementById('sidebarUser').textContent = currentUser.username;

        if (currentUser.role === 'admin') {
            document.getElementById('navPending').style.display = 'flex';
            refreshPendingBadge();
        }
        loadDashboard();
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

// ── Dashboard ──
async function loadDashboard() {
    try {
        const [users, devices] = await Promise.all([
            fetchAPI(`${API}/users/`).catch(() => []),
            fetchAPI(`${API}/devices/`).catch(() => [])
        ]);

        const total    = (users || []).length;
        const pending  = (users || []).filter(u => u.approval_status === 'pending').length;
        const approved = (users || []).filter(u => u.approval_status === 'approved').length;

        document.getElementById('statTotal').textContent   = total;
        document.getElementById('statPending').textContent  = pending;
        document.getElementById('statApproved').textContent = approved;
        document.getElementById('statDevices').textContent  = (devices || []).length;

        const recent = (users || []).slice(0, 6);
        document.getElementById('recentUsersTable').innerHTML = recent.length === 0
            ? '<tr class="empty-row"><td colspan="5">Sin usuarios</td></tr>'
            : recent.map(u => `
                <tr>
                    <td><strong>${u.username}</strong></td>
                    <td>${u.full_name}</td>
                    <td>${u.department || '—'}</td>
                    <td>${statusBadge(u.approval_status)}</td>
                    <td>${fmtDate(u.created_at)}</td>
                </tr>`).join('');
    } catch (e) {
        console.error('Dashboard error', e);
    }
}

function refreshDashboard() { loadDashboard(); }

// ── Pending users (cards) ──
async function loadPendingUsers() {
    const container = document.getElementById('pendingCards');
    container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--text-muted)">Cargando…</div>';

    try {
        const list = await fetchAPI(`${API}/auth/pending-users`) || [];

        if (list.length === 0) {
            container.innerHTML = `
                <div style="padding:3rem;text-align:center;color:var(--text-muted)">
                    <div style="font-size:2.5rem;margin-bottom:.75rem">🎉</div>
                    <strong>Sin solicitudes pendientes</strong>
                    <p style="margin-top:.35rem;font-size:.875rem">Todas las solicitudes han sido procesadas.</p>
                </div>`;
            refreshPendingBadge();
            return;
        }

        container.innerHTML = '<div class="cards-grid">' +
            list.map(u => buildPendingCard(u)).join('') +
        '</div>';

        refreshPendingBadge();
    } catch (e) {
        container.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--danger)">Error al cargar solicitudes.</div>';
    }
}

function buildPendingCard(u) {
    const isVisitor  = u.department === 'Visita / Externo';
    const ticketHtml = (isVisitor && u.ticket_number) ? `
        <div class="card-ticket">
            🎫 Ticket: <strong>${u.ticket_number}</strong>
            ${u.access_duration_hours ? `· ${durationLabel(u.access_duration_hours)}` : ''}
        </div>` : '';

    const deviceHtml = (u.mac_address || u.ip_address || u.device_type) ? `
        <div class="card-device">
            ${u.device_type ? `<div class="card-device-row">💻 <span>${u.device_type}${u.os_type ? ' · ' + u.os_type : ''}${u.os_version ? ' ' + u.os_version : ''}</span></div>` : ''}
            ${u.mac_address ? `<div class="card-device-row">🔑 <span class="mono" style="font-family:monospace;font-size:.79rem">${u.mac_address}</span></div>` : ''}
            ${u.ip_address  ? `<div class="card-device-row">📍 <span>${u.ip_address}</span></div>` : ''}
        </div>` : '';

    const durationDefault = u.access_duration_hours || '';

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
            <div class="card-date">📅 Registrado: ${fmtDateTime(u.created_at)}</div>
        </div>
        <div class="card-footer">
            <button class="btn btn-danger btn-sm" onclick="rejectUser(${u.id})">✕ Rechazar</button>
            <button class="btn btn-success btn-sm" onclick="openApproveModal(${u.id}, '${escAttr(u.full_name)}', '${escAttr(u.department || '')}', '${escAttr(u.position || '')}', ${durationDefault || 'null'})">
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

    const hint = document.getElementById('approveHint');
    if (requestedHours) {
        hint.textContent = `El usuario solicitó ${durationLabel(requestedHours)}. Puedes modificarlo si lo deseas.`;
    } else {
        hint.textContent = 'Dejar en blanco para acceso permanente.';
    }

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
        await fetchAPI(`${API}/auth/approve-user/${pendingApproveId}`, {
            method: 'POST',
            body: JSON.stringify(body)
        });
        closeApproveModal();
        toast('✅ Usuario aprobado correctamente.', 'ok');
        loadPendingUsers();
    } catch (e) {
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

// ── Users table ──
async function loadUsers() {
    try {
        allUsers = await fetchAPI(`${API}/users/`) || [];
        renderUsers(allUsers);
    } catch { /* silent */ }
}

function renderUsers(list) {
    document.getElementById('usersTable').innerHTML = list.length === 0
        ? '<tr class="empty-row"><td colspan="7">Sin usuarios</td></tr>'
        : list.map(u => `
            <tr>
                <td><strong>${escHtml(u.username)}</strong></td>
                <td>${escHtml(u.full_name)}</td>
                <td>${u.department || '—'}</td>
                <td>${u.position || '—'}</td>
                <td>${u.email || '—'}</td>
                <td>${statusBadge(u.approval_status)}</td>
                <td>
                    ${u.approval_status === 'pending' && currentUser?.role === 'admin'
                        ? `<button class="btn btn-success btn-sm" onclick="openApproveModal(${u.id},'${escAttr(u.full_name)}','${escAttr(u.department||'')}','${escAttr(u.position||'')}',${u.access_duration_hours||'null'})">Aprobar</button>`
                        : ''}
                </td>
            </tr>`).join('');
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
        ? '<tr class="empty-row"><td colspan="6">Sin dispositivos</td></tr>'
        : list.map(d => `
            <tr>
                <td>${d.hostname || '—'}</td>
                <td><code style="font-family:monospace;font-size:.82rem">${d.mac_address}</code></td>
                <td>${d.ip_address || '—'}</td>
                <td>${d.device_type || '—'}</td>
                <td>${[d.os_type, d.os_version].filter(Boolean).join(' ') || '—'}</td>
                <td>${fmtDate(d.created_at)}</td>
            </tr>`).join('');
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
        document.getElementById('profileRole').innerHTML = u.role === 'admin'
            ? '<span class="badge badge-admin">Administrador</span>'
            : '<span class="badge badge-user">Usuario</span>';
        document.getElementById('profileFields').innerHTML = [
            ['Usuario',        u.username],
            ['Correo',         u.email || '—'],
            ['Rol',            u.role === 'admin' ? 'Administrador' : 'Usuario'],
            ['Estado',         u.is_active ? 'Activo' : 'Inactivo'],
        ].map(([label, val]) => `
            <div class="profile-field">
                <span class="profile-field-label">${label}</span>
                <span class="profile-field-val">${escHtml(String(val))}</span>
            </div>`).join('');
    } catch { /* silent */ }
}

// ── Utilities ──
function statusBadge(status) {
    const map = {
        pending:  ['badge-pending',  '⏳ Pendiente'],
        approved: ['badge-approved', '✓ Aprobado'],
        rejected: ['badge-rejected', '✕ Rechazado'],
    };
    const [cls, label] = map[status] || ['', status];
    return `<span class="badge ${cls}">${label}</span>`;
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
    return res.json();
}

// Close approve modal on overlay click
document.addEventListener('click', e => {
    const overlay = document.getElementById('approveModal');
    if (e.target === overlay) closeApproveModal();
});
