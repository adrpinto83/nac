/**
 * Dashboard - Métricas y estadísticas en tiempo real
 */

let dashboardRefreshInterval = null;

async function loadDashboard() {
    changePageTitle('Dashboard');
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div class="dashboard-container">
            <div class="metrics-grid" id="metricsGrid">
                <div class="metric-card loading">
                    <div class="spinner"></div>
                    Cargando métricas...
                </div>
            </div>

            <div class="charts-section">
                <div class="chart-container">
                    <h3>Dispositivos Vivos</h3>
                    <canvas id="deviceChart"></canvas>
                </div>

                <div class="chart-container">
                    <h3>Tráfico de Red (Últimas 24h)</h3>
                    <canvas id="trafficChart"></canvas>
                </div>
            </div>

            <div class="top-section">
                <h3>Top 5 Dispositivos por Tráfico</h3>
                <table id="topDevicesTable" class="table">
                    <thead>
                        <tr>
                            <th>Dispositivo</th>
                            <th>Usuario</th>
                            <th>Entrada (MB)</th>
                            <th>Salida (MB)</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <div class="alerts-section">
                <h3>⚠️ Alertas Recientes</h3>
                <div id="alertsContainer" class="alerts-list"></div>
            </div>
        </div>
    `;

    await refreshDashboard();

    // Actualizar cada 30 segundos
    if (dashboardRefreshInterval) clearInterval(dashboardRefreshInterval);
    dashboardRefreshInterval = setInterval(refreshDashboard, 30000);
}

async function refreshDashboard() {
    try {
        // Obtener métricas
        const metrics = await API.getMetrics();
        displayMetrics(metrics);

        // Obtener top dispositivos
        const topDevices = await API.getTopDevices(5);
        displayTopDevices(topDevices);

        // Obtener alertas
        const alerts = await API.getAlerts();
        displayAlerts(alerts);

        // Actualizar estado del router
        updateRouterStatus(metrics.router_status, metrics.router_latency_ms);
    } catch (error) {
        console.error('Error actualizando dashboard:', error);
        showNotification('Error al actualizar dashboard', 'error');
    }
}

function displayMetrics(metrics) {
    const grid = document.getElementById('metricsGrid');

    const html = `
        <div class="metric-card success">
            <div class="metric-value">${metrics.total_registered_devices}</div>
            <div class="metric-label">Dispositivos Registrados</div>
        </div>

        <div class="metric-card info">
            <div class="metric-value">${metrics.active_devices_now}</div>
            <div class="metric-label">Dispositivos Activos Ahora</div>
        </div>

        <div class="metric-card warning">
            <div class="metric-value">${metrics.suspended_devices}</div>
            <div class="metric-label">Suspendidos</div>
        </div>

        <div class="metric-card error">
            <div class="metric-value">${metrics.expired_devices}</div>
            <div class="metric-label">Expirados</div>
        </div>

        <div class="metric-card">
            <div class="metric-value">${metrics.unregistered_macs}</div>
            <div class="metric-label">MACs No Registradas</div>
        </div>

        <div class="metric-card">
            <div class="metric-value">${metrics.router_latency_ms.toFixed(1)}ms</div>
            <div class="metric-label">Latencia Router</div>
        </div>
    `;

    grid.innerHTML = html;
}

function displayTopDevices(devices) {
    const tbody = document.querySelector('#topDevicesTable tbody');

    if (devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Sin datos</td></tr>';
        return;
    }

    const rows = devices.map(device => `
        <tr>
            <td><strong>${device.device_name}</strong></td>
            <td>${device.full_name || '-'}</td>
            <td>${(device.bytes_in / 1024 / 1024).toFixed(2)}</td>
            <td>${(device.bytes_out / 1024 / 1024).toFixed(2)}</td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

function displayAlerts(alerts) {
    const container = document.getElementById('alertsContainer');

    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay alertas</p>';
        return;
    }

    const html = alerts.slice(0, 10).map(alert => {
        const levelClass = {
            'info': 'alert-info',
            'warning': 'alert-warning',
            'error': 'alert-error',
            'critical': 'alert-critical'
        }[alert.level] || 'alert-info';

        return `
            <div class="alert ${levelClass}">
                <strong>${alert.level.toUpperCase()}</strong>: ${alert.message}
                <small>${new Date(alert.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

function updateRouterStatus(status, latency) {
    const statusEl = document.getElementById('routerStatus');
    if (statusEl) {
        const icon = status === 'ok' ? '✅' : '❌';
        statusEl.textContent = `${icon} ${latency.toFixed(1)}ms`;
        statusEl.className = `router-status status-${status}`;
    }
}
