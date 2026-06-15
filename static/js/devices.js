/**
 * Gestión de Dispositivos
 */

async function loadDevices() {
    changePageTitle('Dispositivos');
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div class="page-container">
            <div class="page-header">
                <h2>Dispositivos Registrados</h2>
                <button class="btn btn-primary" onclick="openModal('deviceModal')">+ Registrar Dispositivo</button>
            </div>

            <div class="tabs">
                <button class="tab-btn active" onclick="switchDeviceTab('registered')">Registrados</button>
                <button class="tab-btn" onclick="switchDeviceTab('live')">Vivos en Red</button>
            </div>

            <table class="table" id="devicesTable">
                <thead>
                    <tr>
                        <th>MAC Address</th>
                        <th>Nombre</th>
                        <th>Usuario</th>
                        <th>IP Asignada</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="6" class="loading">Cargando dispositivos...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    await refreshDevices();
    setupDeviceForm();
}

async function refreshDevices() {
    try {
        const devices = await API.listDevices();
        displayDevicesList(devices);
    } catch (error) {
        showNotification('Error al cargar dispositivos', 'error');
    }
}

function displayDevicesList(devices) {
    const tbody = document.querySelector('#devicesTable tbody');

    if (devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Sin dispositivos</td></tr>';
        return;
    }

    const rows = devices.map(device => `
        <tr>
            <td><code>${device.mac_address}</code></td>
            <td><strong>${device.device_name}</strong></td>
            <td>${device.full_name || '-'}</td>
            <td>${device.assigned_ip || '-'}</td>
            <td><span class="status status-${device.status}">${device.status}</span></td>
            <td class="actions">
                ${device.status === 'active' ? 
                    `<button class="btn-sm" onclick="blockDeviceAction(${device.id})">🚫</button>` :
                    `<button class="btn-sm" onclick="unblockDeviceAction(${device.id})">✅</button>`
                }
                <button class="btn-sm" onclick="deleteDeviceAction(${device.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

async function switchDeviceTab(tab) {
    if (tab === 'registered') {
        await loadDevices();
    } else if (tab === 'live') {
        await loadLiveDevices();
    }
}

async function loadLiveDevices() {
    try {
        const devices = await API.getLiveDevices();
        displayLiveDevicesList(devices);
    } catch (error) {
        showNotification('Error al obtener dispositivos vivos', 'error');
    }
}

function displayLiveDevicesList(devices) {
    const tbody = document.querySelector('#devicesTable tbody');

    if (devices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Sin dispositivos en la red</td></tr>';
        return;
    }

    const rows = devices.map(device => `
        <tr>
            <td><code>${device.mac_address}</code></td>
            <td>${device.mac_address.slice(-8)}</td>
            <td>${device.ip_address}</td>
            <td>${device.interface}</td>
            <td>${device.is_registered ? '✅ Registrado' : '⚠️ No registrado'}</td>
            <td class="actions">
                <button class="btn-sm" onclick="registerLiveDevice('${device.mac_address}')">Registrar</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

function setupDeviceForm() {
    const form = document.getElementById('deviceForm');
    
    // Cargar usuarios
    API.listUsers().then(users => {
        const select = form.querySelector('select[name="user_id"]');
        select.innerHTML = users.map(u => 
            `<option value="${u.id}">${u.full_name} (${u.username})</option>`
        ).join('');
    });

    // Cargar perfiles
    API.listProfiles().then(profiles => {
        const select = form.querySelector('select[name="profile_id"]');
        select.innerHTML = '<option value="">-- Sin perfil --</option>' +
            profiles.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    });

    form.onsubmit = async (e) => {
        e.preventDefault();

        const formData = {
            mac_address: form.mac_address.value,
            device_name: form.device_name.value,
            user_id: parseInt(form.user_id.value),
            profile_id: form.profile_id.value ? parseInt(form.profile_id.value) : null,
        };

        try {
            await API.registerDevice(formData);
            closeModal('deviceModal');
            form.reset();
            loadDevices();
            showNotification('Dispositivo registrado exitosamente', 'success');
        } catch (error) {
            showNotification('Error: ' + error.message, 'error');
        }
    };
}

async function blockDeviceAction(deviceId) {
    if (confirm('¿Bloquear este dispositivo?')) {
        try {
            await API.blockDevice(deviceId);
            loadDevices();
            showNotification('Dispositivo bloqueado', 'success');
        } catch (error) {
            showNotification('Error al bloquear', 'error');
        }
    }
}

async function unblockDeviceAction(deviceId) {
    if (confirm('¿Desbloquear este dispositivo?')) {
        try {
            await API.unblockDevice(deviceId);
            loadDevices();
            showNotification('Dispositivo desbloqueado', 'success');
        } catch (error) {
            showNotification('Error al desbloquear', 'error');
        }
    }
}

async function deleteDeviceAction(deviceId) {
    if (confirm('¿Eliminar este dispositivo?')) {
        try {
            await API.deleteDevice(deviceId);
            loadDevices();
            showNotification('Dispositivo eliminado', 'success');
        } catch (error) {
            showNotification('Error al eliminar', 'error');
        }
    }
}
