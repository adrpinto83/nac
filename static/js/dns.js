/**
 * Gestión de Bloqueos DNS
 */

async function loadDNS() {
    changePageTitle('Bloqueos DNS');
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div class="page-container">
            <div class="page-header">
                <h2>Dominios Bloqueados</h2>
                <button class="btn btn-primary" onclick="openDNSModal()">+ Agregar Bloqueo</button>
            </div>

            <div class="tabs">
                <button class="tab-btn active" onclick="switchDNSTab('entries')">Dominios</button>
                <button class="tab-btn" onclick="switchDNSTab('categories')">Categorías</button>
            </div>

            <table class="table" id="dnsTable">
                <thead>
                    <tr>
                        <th>Dominio</th>
                        <th>Categoría</th>
                        <th>Estado</th>
                        <th>Comentario</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="5" class="loading">Cargando dominios...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    await loadDNSEntries();
}

async function loadDNSEntries() {
    try {
        const entries = await API.listDNSEntries();
        displayDNSEntries(entries);
    } catch (error) {
        showNotification('Error al cargar dominios', 'error');
    }
}

function displayDNSEntries(entries) {
    const tbody = document.querySelector('#dnsTable tbody');

    if (entries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">Sin dominios bloqueados</td></tr>';
        return;
    }

    const rows = entries.map(entry => `
        <tr>
            <td><code>${entry.domain}</code></td>
            <td>${entry.category_id || '-'}</td>
            <td><span class="status status-${entry.enabled ? 'active' : 'inactive'}">
                ${entry.enabled ? 'Activo' : 'Inactivo'}
            </span></td>
            <td>${entry.comment || '-'}</td>
            <td class="actions">
                <button class="btn-sm" onclick="deleteDNSEntry(${entry.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

function openDNSModal() {
    const domain = prompt('Dominio a bloquear (ej: facebook.com):');
    if (!domain) return;

    const comment = prompt('Comentario (opcional):');

    API.createDNSEntry({
        domain,
        comment: comment || null,
    }).then(() => {
        loadDNS();
        showNotification('Dominio bloqueado', 'success');
    }).catch(e => showNotification('Error: ' + e.message, 'error'));
}

async function switchDNSTab(tab) {
    if (tab === 'entries') {
        await loadDNS();
    } else {
        await loadDNSCategories();
    }
}

async function loadDNSCategories() {
    try {
        const categories = await API.listDNSCategories();
        displayDNSCategories(categories);
    } catch (error) {
        showNotification('Error al cargar categorías', 'error');
    }
}

function displayDNSCategories(categories) {
    const tbody = document.querySelector('#dnsTable tbody');
    const rows = categories.map(cat => `
        <tr>
            <td><strong>${cat.name}</strong></td>
            <td colspan="3">${cat.description || '-'}</td>
            <td class="actions">
                <button class="btn-sm" onclick="deleteCategory(${cat.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows || '<tr><td colspan="5" class="text-center">Sin categorías</td></tr>';
}

async function deleteDNSEntry(entryId) {
    if (confirm('¿Eliminar este bloqueo?')) {
        try {
            await API.deleteDNSEntry(entryId);
            loadDNS();
            showNotification('Bloqueo eliminado', 'success');
        } catch (error) {
            showNotification('Error al eliminar', 'error');
        }
    }
}
