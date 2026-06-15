// app.js — MikroTik NAC Control Panel

const API_BASE = '/api';
let token = localStorage.getItem('token');
let currentUser = null;

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        showMainApp();
        loadCurrentUser();
        loadDashboard();
    } else {
        showLoginPage();
    }

    // Auto-refresh dashboard
    setInterval(() => {
        if (document.getElementById('dashboardContent')?.classList.contains('active')) {
            loadDashboard();
        }
    }, 30000);
});

// ============ PAGE NAVIGATION ============
function showLoginPage() {
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('mainApp').classList.remove('active');
}

function showMainApp() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('mainApp').classList.add('active');
}

function navigateTo(page) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(el => {
        el.classList.remove('active');
    });

    // Update nav items
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('active');
        if (el.getAttribute('data-page') === page) {
            el.classList.add('active');
        }
    });

    // Show requested section
    const contentId = page + 'Content';
    const element = document.getElementById(contentId);
    if (element) {
        element.classList.add('active');
    }

    // Update breadcrumb
    const pageNames = {
        'dashboard': 'Dashboard',
        'users': 'Usuarios',
        'operators': 'Operadores',
        'dns': 'DNS',
        'qos': 'Ancho de Banda',
        'audit': 'Auditoría'
    };
    const breadcrumb = document.getElementById('breadcrumb');
    if (breadcrumb) {
        breadcrumb.textContent = pageNames[page] || 'Panel';
    }

    // Close sidebar on mobile
    const sidebar = document.getElementById('sidebar');
    if (sidebar?.classList.contains('open')) {
        sidebar.classList.remove('open');
    }

    // Load content
    switch(page) {
        case 'dashboard': loadDashboard(); break;
        case 'users': loadUsers(); break;
        case 'operators': loadOperators(); break;
        case 'dns': loadDNSCategories(); break;
        case 'qos': loadQoSProfiles(); break;
        case 'audit': loadAuditLog(); break;
    }
}

function toggleSidebar() {
    document.getElementById('sidebar')?.classList.toggle('open');
}

// ============ AUTHENTICATION ============
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            errorDiv.textContent = '❌ Usuario o contraseña inválidos';
            errorDiv.style.display = 'block';
            return;
        }

        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);

        showMainApp();
        loadCurrentUser();
        loadDashboard();
        errorDiv.style.display = 'none';
    } catch (error) {
        errorDiv.textContent = '❌ Error de conexión: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

async function handleLogout() {
    localStorage.removeItem('token');
    token = null;
    showLoginPage();
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

async function loadCurrentUser() {
    try {
        const response = await apiFetch(`${API_BASE}/auth/me`);
        currentUser = response;

        const userDisplay = document.getElementById('currentUser');
        if (userDisplay) {
            userDisplay.textContent = response.username || response.full_name || 'Usuario';
        }

        // Show admin menus
        if (response.role === 'ADMIN' || response.role === 'SUPERADMIN') {
            document.getElementById('adminLink')?.style.setProperty('display', 'flex');
            document.getElementById('dnsLink')?.style.setProperty('display', 'flex');
            document.getElementById('qosLink')?.style.setProperty('display', 'flex');
        }
    } catch (error) {
        console.error('Error loading user:', error);
        handleLogout();
    }
}

// ============ DASHBOARD ============
async function loadDashboard() {
    try {
        const stats = await apiFetch(`${API_BASE}/dashboard/metrics`);

        document.getElementById('totalUsers').textContent = stats.total_users || 0;
        document.getElementById('activeUsers').textContent = stats.active_users || 0;
        document.getElementById('totalDevices').textContent = stats.total_devices || 0;
        document.getElementById('systemStatus').textContent = stats.system_status || '✅ OK';

        // Top consumers
        const tbody = document.getElementById('topConsumersBody');
        tbody.innerHTML = '';
        if (stats.top_consumers?.length > 0) {
            stats.top_consumers.forEach(item => {
                tbody.innerHTML += `
                    <tr>
                        <td>${item.full_name || item.device_name || '-'}</td>
                        <td><code>${item.mac_address || '-'}</code></td>
                        <td>${formatBytes((item.bytes_in || 0) + (item.bytes_out || 0))}</td>
                    </tr>
                `;
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Sin datos</td></tr>';
        }

        // Expiring users
        const expBody = document.getElementById('expiringBody');
        expBody.innerHTML = '';
        if (stats.expiring_soon?.length > 0) {
            stats.expiring_soon.forEach(user => {
                expBody.innerHTML += `
                    <tr>
                        <td>${user.full_name || '-'}</td>
                        <td>${user.cedula || '-'}</td>
                        <td>${user.expires_at ? new Date(user.expires_at).toLocaleDateString('es-ES') : '-'}</td>
                    </tr>
                `;
            });
        } else {
            expBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Sin expiraciones próximas</td></tr>';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// ============ USERS ============
async function loadUsers() {
    try {
        const users = await apiFetch(`${API_BASE}/users/`);
        const tbody = document.getElementById('usersBody');
        tbody.innerHTML = '';

        if (!users?.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No hay usuarios</td></tr>';
            return;
        }

        users.forEach(user => {
            const statusClass = user.status === 'activo' ? 'success' : 'danger';
            tbody.innerHTML += `
                <tr>
                    <td><strong>${user.full_name || '-'}</strong></td>
                    <td>${user.cedula || '-'}</td>
                    <td><code>${user.mac_address || '-'}</code></td>
                    <td>${user.profile || '-'}</td>
                    <td><span class="badge badge-${statusClass}">${user.status || '?'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="editUser(${user.id})" title="Editar">✎</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})" title="Eliminar">✕</button>
                    </td>
                </tr>
            `;
        });

        window.allUsers = users;
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersBody').innerHTML = '<tr><td colspan="6" class="text-center text-muted">Error</td></tr>';
    }
}

function toggleUserForm() {
    const form = document.getElementById('userFormContainer');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
    if (form.style.display === 'block') {
        document.getElementById('userForm').reset();
    }
}

async function handleCreateUser(event) {
    event.preventDefault();

    const userData = {
        full_name: document.getElementById('fullName').value,
        cedula: document.getElementById('cedula').value,
        mac_address: document.getElementById('macAddress').value,
        profile: document.getElementById('profile').value,
        cargo: document.getElementById('cargo').value || null,
        email: document.getElementById('email').value || null,
        phone: document.getElementById('phone').value || null
    };

    try {
        await apiFetch(`${API_BASE}/users/`, {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        alert('✅ Usuario creado');
        toggleUserForm();
        loadUsers();
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

function filterUsers() {
    const search = document.getElementById('userSearch').value.toLowerCase();
    const status = document.getElementById('userStatusFilter').value;

    document.querySelectorAll('#usersBody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        const statusCell = row.querySelectorAll('td')[4]?.textContent || '';
        const match = text.includes(search) && (!status || statusCell.includes(status));
        row.style.display = match ? '' : 'none';
    });
}

async function editUser(userId) {
    const newProfile = prompt('Nuevo perfil (ADMIN/PROFESIONAL/ESTANDAR/INVITADO):');
    if (!newProfile) return;

    try {
        await apiFetch(`${API_BASE}/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ profile: newProfile })
        });
        alert('✅ Usuario actualizado');
        loadUsers();
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

async function deleteUser(userId) {
    if (!confirm('¿Eliminar usuario?')) return;

    try {
        await apiFetch(`${API_BASE}/users/${userId}`, { method: 'DELETE' });
        alert('✅ Usuario eliminado');
        loadUsers();
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

// ============ OPERATORS ============
async function loadOperators() {
    try {
        const response = await apiFetch(`${API_BASE}/auth/operators`);
        const operators = Array.isArray(response) ? response : [];
        const tbody = document.getElementById('operatorsBody');
        tbody.innerHTML = '';

        if (!operators.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No hay operadores</td></tr>';
            return;
        }

        operators.forEach(op => {
            tbody.innerHTML += `
                <tr>
                    <td><strong>${op.username || '-'}</strong></td>
                    <td>${op.full_name || '-'}</td>
                    <td>${op.role || 'SOPORTE'}</td>
                    <td>${op.enabled ? '✅ Activo' : '❌ Inactivo'}</td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('Error loading operators:', error);
        document.getElementById('operatorsBody').innerHTML = '<tr><td colspan="4" class="text-center text-muted">Error</td></tr>';
    }
}

function toggleOperatorForm() {
    const form = document.getElementById('operatorFormContainer');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
    if (form.style.display === 'block') {
        document.getElementById('operatorForm').reset();
    }
}

async function handleCreateOperator(event) {
    event.preventDefault();

    const opData = {
        username: document.getElementById('opUsername').value,
        password: document.getElementById('opPassword').value,
        full_name: document.getElementById('opFullName').value,
        role: document.getElementById('opRole').value
    };

    try {
        await apiFetch(`${API_BASE}/auth/operators`, {
            method: 'POST',
            body: JSON.stringify(opData)
        });
        alert('✅ Operador creado');
        toggleOperatorForm();
        loadOperators();
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
}

// ============ DNS ============
async function loadDNSCategories() {
    try {
        const categories = await apiFetch(`${API_BASE}/dns/categories`);
        const container = document.getElementById('categoriesContainer');
        container.innerHTML = '';

        if (!categories?.length) {
            container.innerHTML = '<p class="text-muted">No hay categorías</p>';
            return;
        }

        categories.forEach(cat => {
            container.innerHTML += `
                <div class="badge badge-info" style="display: block; margin: 5px 0;">
                    <strong>${cat.name}</strong> - ${cat.description || 'Sin descripción'}
                </div>
            `;
        });
    } catch (error) {
        console.error('Error loading DNS:', error);
    }
}

// ============ QoS ============
async function loadQoSProfiles() {
    try {
        const profiles = await apiFetch(`${API_BASE}/qos/profiles`);
        const tbody = document.getElementById('profilesBody');
        tbody.innerHTML = '';

        if (!profiles?.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No hay perfiles</td></tr>';
            return;
        }

        profiles.forEach(profile => {
            tbody.innerHTML += `
                <tr>
                    <td><strong>${profile.name || '-'}</strong></td>
                    <td>${profile.max_limit_down || '-'}</td>
                    <td>${profile.max_limit_up || '-'}</td>
                    <td>${profile.priority || '-'}</td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('Error loading QoS:', error);
    }
}

// ============ AUDIT ============
async function loadAuditLog() {
    try {
        const logs = await apiFetch(`${API_BASE}/stats/dashboard`);
        const tbody = document.getElementById('auditBody');
        tbody.innerHTML = '';

        if (!logs?.audit_log?.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Sin registros</td></tr>';
            return;
        }

        logs.audit_log.forEach(log => {
            tbody.innerHTML += `
                <tr>
                    <td>${new Date(log.timestamp || Date.now()).toLocaleString('es-ES')}</td>
                    <td>${log.operator_id || '-'}</td>
                    <td>${log.action || '-'}</td>
                    <td>${log.entity_type || '-'}</td>
                    <td><span class="badge badge-success">${log.result || 'OK'}</span></td>
                </tr>
            `;
        });

        window.allLogs = logs.audit_log;
    } catch (error) {
        console.error('Error loading audit:', error);
    }
}

function filterAudit() {
    const search = document.getElementById('auditSearch').value.toLowerCase();
    document.querySelectorAll('#auditBody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(search) ? '' : 'none';
    });
}

// ============ UTILITIES ============
async function apiFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, {
        ...options,
        headers: { ...headers, ...options.headers }
    });

    if (response.status === 401) {
        handleLogout();
        throw new Error('Sesión expirada');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Error ${response.status}`);
    }

    return response.json();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}
