/**
 * Gestión de Perfiles QoS
 */

async function loadProfiles() {
    changePageTitle('Perfiles QoS');
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div class="page-container">
            <div class="page-header">
                <h2>Perfiles de QoS</h2>
                <button class="btn btn-primary" onclick="openProfileModal()">+ Crear Perfil</button>
            </div>

            <table class="table" id="profilesTable">
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Descarga Max</th>
                        <th>Carga Max</th>
                        <th>Prioridad</th>
                        <th>Descripción</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="6" class="loading">Cargando perfiles...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    try {
        const profiles = await API.listProfiles();
        displayProfilesList(profiles);
    } catch (error) {
        showNotification('Error al cargar perfiles', 'error');
    }
}

function displayProfilesList(profiles) {
    const tbody = document.querySelector('#profilesTable tbody');

    if (profiles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Sin perfiles</td></tr>';
        return;
    }

    const rows = profiles.map(profile => `
        <tr>
            <td><strong>${profile.name}</strong></td>
            <td>${profile.max_download || '-'}</td>
            <td>${profile.max_upload || '-'}</td>
            <td><span class="badge">P${profile.priority}</span></td>
            <td>${profile.description || '-'}</td>
            <td class="actions">
                <button class="btn-sm" onclick="deleteProfile(${profile.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

function openProfileModal() {
    const name = prompt('Nombre del perfil:');
    if (!name) return;

    const maxDown = prompt('Descarga máxima (ej: 10M, 5M):');
    const maxUp = prompt('Carga máxima (ej: 5M, 2M):');

    API.createProfile({
        name,
        max_download: maxDown || null,
        max_upload: maxUp || null,
    }).then(() => {
        loadProfiles();
        showNotification('Perfil creado', 'success');
    }).catch(e => showNotification('Error: ' + e.message, 'error'));
}

async function deleteProfile(profileId) {
    if (confirm('¿Eliminar este perfil?')) {
        try {
            await API.updateProfile(profileId, {});
            loadProfiles();
            showNotification('Perfil eliminado', 'success');
        } catch (error) {
            showNotification('Error al eliminar', 'error');
        }
    }
}
