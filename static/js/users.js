/**
 * Gestión de Usuarios
 */

async function loadUsers() {
    changePageTitle('Usuarios');
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div class="page-container">
            <div class="page-header">
                <h2>Gestión de Usuarios</h2>
                <button class="btn btn-primary" onclick="openModal('userModal')">+ Crear Usuario</button>
            </div>

            <table class="table" id="usersTable">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Nombre</th>
                        <th>Cédula</th>
                        <th>Email</th>
                        <th>Rol</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="7" class="loading">Cargando usuarios...</td></tr>
                </tbody>
            </table>
        </div>
    `;

    try {
        const users = await API.listUsers();
        displayUsersList(users);
        setupUserForm();
    } catch (error) {
        showNotification('Error al cargar usuarios', 'error');
    }
}

function displayUsersList(users) {
    const tbody = document.querySelector('#usersTable tbody');

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Sin usuarios</td></tr>';
        return;
    }

    const rows = users.map(user => `
        <tr>
            <td><strong>${user.username}</strong></td>
            <td>${user.full_name}</td>
            <td>${user.cedula || '-'}</td>
            <td>${user.email || '-'}</td>
            <td><span class="badge">${user.role}</span></td>
            <td><span class="status status-${user.status}">${user.status}</span></td>
            <td class="actions">
                <button class="btn-sm" onclick="suspendUserAction(${user.id})">🔒</button>
                <button class="btn-sm" onclick="deleteUserAction(${user.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = rows;
}

function setupUserForm() {
    const form = document.getElementById('userForm');
    form.onsubmit = async (e) => {
        e.preventDefault();

        const formData = {
            username: form.username.value,
            password: form.password.value,
            full_name: form.full_name.value,
            cedula: form.cedula.value || null,
            email: form.email.value || null,
        };

        try {
            await API.createUser(formData);
            closeModal('userModal');
            form.reset();
            loadUsers();
            showNotification('Usuario creado exitosamente', 'success');
        } catch (error) {
            showNotification('Error al crear usuario: ' + error.message, 'error');
        }
    };
}

async function suspendUserAction(userId) {
    if (confirm('¿Suspender este usuario?')) {
        try {
            await API.suspendUser(userId);
            loadUsers();
            showNotification('Usuario suspendido', 'success');
        } catch (error) {
            showNotification('Error al suspender usuario', 'error');
        }
    }
}

async function deleteUserAction(userId) {
    if (confirm('¿Eliminar este usuario y sus dispositivos?')) {
        try {
            await API.deleteUser(userId);
            loadUsers();
            showNotification('Usuario eliminado', 'success');
        } catch (error) {
            showNotification('Error al eliminar usuario', 'error');
        }
    }
}
