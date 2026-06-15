// ============== STATE ==============
let token = localStorage.getItem('token');
let currentUser = null;
let allUsers = [];
let allDevices = [];

// ============== API BASE ==============
const API_BASE = window.location.origin + '/api';

// ============== INITIALIZATION ==============
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        showApp();
        loadDashboard();
    } else {
        showLogin();
    }
});

// ============== AUTH ==============
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            token = data.access_token;
            localStorage.setItem('token', token);
            showApp();
            loadDashboard();
        } else {
            showError(data.detail || 'Login failed');
        }
    } catch (error) {
        showError('Network error');
    }
}

function handleLogout() {
    token = null;
    localStorage.removeItem('token');
    showLogin();
    document.getElementById('loginForm').reset();
}

// ============== UI NAVIGATION ==============
function showLogin() {
    document.getElementById('loginContainer').style.display = 'flex';
    document.getElementById('appContainer').style.display = 'none';
}

function showApp() {
    document.getElementById('loginContainer').style.display = 'none';
    document.getElementById('appContainer').style.display = 'flex';
}

function navigateTo(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');

    // Show page
    document.getElementById(page + 'Page').classList.add('active');

    // Load data
    if (page === 'dashboard') loadDashboard();
    if (page === 'users') loadUsers();
    if (page === 'devices') loadDevices();
    if (page === 'profile') loadProfile();
}

// ============== DASHBOARD ==============
async function loadDashboard() {
    try {
        const [usersRes, devicesRes] = await Promise.all([
            fetchAPI(`${API_BASE}/users/`),
            fetchAPI(`${API_BASE}/devices/`)
        ]);

        const users = usersRes || [];
        const devices = devicesRes || [];

        const activeDevices = devices.filter(d => d.status === 'online').length;
        const inactiveDevices = devices.filter(d => d.status !== 'online').length;

        document.getElementById('totalUsers').textContent = users.length;
        document.getElementById('totalDevices').textContent = devices.length;
        document.getElementById('activeDevices').textContent = activeDevices;
        document.getElementById('inactiveDevices').textContent = inactiveDevices;

        // Show recent users
        const recentUsers = users.slice(0, 5);
        document.getElementById('recentUsers').innerHTML = recentUsers.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>${user.full_name}</td>
                <td>${user.department || '-'}</td>
                <td>${devices.filter(d => d.user_id === user.id).length}</td>
                <td><button class="btn btn-primary" onclick="openUserDetail(${user.id})">View</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

// ============== USERS ==============
async function loadUsers() {
    try {
        allUsers = await fetchAPI(`${API_BASE}/users/`) || [];
        displayUsers(allUsers);
    } catch (error) {
        console.error('Users load error:', error);
    }
}

function displayUsers(users) {
    document.getElementById('usersTable').innerHTML = users.map(user => `
        <tr>
            <td>${user.username}</td>
            <td>${user.full_name}</td>
            <td>${user.email || '-'}</td>
            <td>${user.phone || '-'}</td>
            <td>${user.department || '-'}</td>
            <td><button class="btn btn-primary" onclick="openUserDetail(${user.id})">View Devices</button></td>
            <td>
                <button class="btn btn-danger" onclick="deleteUser(${user.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function filterUsers() {
    const query = document.getElementById('userSearch').value.toLowerCase();
    const filtered = allUsers.filter(u =>
        u.username.toLowerCase().includes(query) ||
        u.full_name.toLowerCase().includes(query) ||
        (u.email && u.email.toLowerCase().includes(query))
    );
    displayUsers(filtered);
}

function openUserModal() {
    document.getElementById('userForm').reset();
    document.getElementById('userModal').classList.add('active');
}

async function handleCreateUser(e) {
    e.preventDefault();

    const userData = {
        username: document.getElementById('formUsername').value,
        password: document.getElementById('formPassword').value,
        full_name: document.getElementById('formFullName').value,
        email: document.getElementById('formEmail').value,
        phone: document.getElementById('formPhone').value,
        department: document.getElementById('formDepartment').value,
        position: document.getElementById('formPosition').value,
        company: document.getElementById('formCompany').value
    };

    try {
        await fetchAPI(`${API_BASE}/users/`, {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        closeModal('userModal');
        loadUsers();
        alert('User created successfully!');
    } catch (error) {
        alert('Error creating user');
    }
}

async function deleteUser(userId) {
    if (!confirm('Delete this user and all devices?')) return;

    try {
        await fetchAPI(`${API_BASE}/users/${userId}`, { method: 'DELETE' });
        loadUsers();
        alert('User deleted successfully!');
    } catch (error) {
        alert('Error deleting user');
    }
}

async function openUserDetail(userId) {
    try {
        const user = await fetchAPI(`${API_BASE}/users/${userId}`);
        if (user) {
            alert(`${user.full_name}\n\nDepartment: ${user.department}\nDevices: ${user.device_count}\n\nEmail: ${user.email}\nPhone: ${user.phone}`);
        }
    } catch (error) {
        alert('Error loading user details');
    }
}

// ============== DEVICES ==============
async function loadDevices() {
    try {
        allDevices = await fetchAPI(`${API_BASE}/devices/`) || [];
        displayDevices(allDevices);
    } catch (error) {
        console.error('Devices load error:', error);
    }
}

function displayDevices(devices) {
    document.getElementById('devicesTable').innerHTML = devices.map(device => `
        <tr>
            <td>${device.hostname}</td>
            <td><code>${device.mac_address}</code></td>
            <td>${device.user_id}</td>
            <td>${device.device_type}</td>
            <td>${device.manufacturer || '-'}</td>
            <td>${device.model || '-'}</td>
            <td><span class="${device.status === 'online' ? 'text-success' : 'text-danger'}">${device.status}</span></td>
            <td>
                <button class="btn btn-danger" onclick="deleteDevice(${device.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function filterDevices() {
    const query = document.getElementById('deviceSearch').value.toLowerCase();
    const filtered = allDevices.filter(d =>
        d.mac_address.toLowerCase().includes(query) ||
        d.hostname.toLowerCase().includes(query)
    );
    displayDevices(filtered);
}

function openDeviceModal() {
    document.getElementById('deviceForm').reset();
    document.getElementById('deviceModal').classList.add('active');
}

async function handleCreateDevice(e) {
    e.preventDefault();

    const deviceData = {
        user_id: parseInt(document.getElementById('formDeviceUserId').value),
        mac_address: document.getElementById('formMac').value,
        hostname: document.getElementById('formHostname').value,
        device_type: document.getElementById('formDeviceType').value,
        manufacturer: document.getElementById('formManufacturer').value,
        model: document.getElementById('formModel').value,
        os_type: document.getElementById('formOsType').value,
        os_version: document.getElementById('formOsVersion').value
    };

    try {
        await fetchAPI(`${API_BASE}/devices/`, {
            method: 'POST',
            body: JSON.stringify(deviceData)
        });

        closeModal('deviceModal');
        loadDevices();
        alert('Device registered successfully!');
    } catch (error) {
        alert('Error registering device');
    }
}

async function deleteDevice(deviceId) {
    if (!confirm('Delete this device?')) return;

    try {
        await fetchAPI(`${API_BASE}/devices/${deviceId}`, { method: 'DELETE' });
        loadDevices();
        alert('Device deleted successfully!');
    } catch (error) {
        alert('Error deleting device');
    }
}

// ============== PROFILE ==============
async function loadProfile() {
    try {
        const user = await fetchAPI(`${API_BASE}/auth/me`);
        if (user) {
            document.getElementById('userDisplay').textContent = user.username;
            document.getElementById('profileContent').innerHTML = `
                <h2>${user.full_name}</h2>
                <p><strong>Username:</strong> ${user.username}</p>
                <p><strong>Email:</strong> ${user.email || 'Not set'}</p>
                <p><strong>Phone:</strong> ${user.phone || 'Not set'}</p>
                <p><strong>Department:</strong> ${user.department || 'Not set'}</p>
                <p><strong>Position:</strong> ${user.position || 'Not set'}</p>
                <p><strong>Company:</strong> ${user.company || 'Not set'}</p>
                <p><strong>Role:</strong> <strong class="text-success">${user.role}</strong></p>
            `;
        }
    } catch (error) {
        console.error('Profile load error:', error);
    }
}

// ============== MODALS ==============
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// ============== UTILITIES ==============
async function fetchAPI(url, options = {}) {
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
        throw new Error('Unauthorized');
    }

    return response.json();
}

function showError(message) {
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}
