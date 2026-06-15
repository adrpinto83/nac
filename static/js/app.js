/**
 * Aplicación Principal
 */

// Navegar entre páginas
function navigateTo(page) {
    switch(page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'devices':
            loadDevices();
            break;
        case 'users':
            loadUsers();
            break;
        case 'profiles':
            loadProfiles();
            break;
        case 'dns':
            loadDNS();
            break;
        case 'alerts':
            loadAlerts();
            break;
    }

    // Actualizar nav activo
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
}

function changePageTitle(title) {
    document.getElementById('pageTitle').textContent = title;
}

// Modales
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Notificaciones
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    container.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Actualizar datos
document.getElementById('refreshBtn').addEventListener('click', () => {
    const currentPage = document.querySelector('.nav-item.active')?.dataset.page || 'dashboard';
    navigateTo(currentPage);
    showNotification('Datos actualizados', 'info');
});

// Cerrar sesión
document.getElementById('logoutBtn').addEventListener('click', handleLogout);

// Navegar
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(item.dataset.page);
    });
});

// Tema oscuro
document.getElementById('themeToggleBtn').addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
});

// Restaurar tema
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
}

// Auxiliar para alertas
async function loadAlerts() {
    changePageTitle('Alertas');
    const contentArea = document.getElementById('contentArea');

    try {
        const alerts = await API.getAlerts();
        contentArea.innerHTML = `
            <div class="page-container">
                <h2>Alertas del Sistema</h2>
                <div class="alerts-list">
                    ${alerts.length === 0 ? '<p>No hay alertas</p>' : 
                        alerts.map(alert => `
                        <div class="alert alert-${alert.level}">
                            <strong>${alert.level.toUpperCase()}</strong>: ${alert.message}
                            <small>${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (error) {
        showNotification('Error al cargar alertas', 'error');
    }
}
