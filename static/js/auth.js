/**
 * Gestión de autenticación
 */

let currentUser = null;

async function initAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        showLoginPage();
        return;
    }

    try {
        currentUser = await API.getCurrentUser();
        showMainApp();
    } catch (error) {
        localStorage.removeItem('token');
        showLoginPage();
    }
}

async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const response = await API.login(username, password);
        currentUser = response.user;
        showMainApp();
    } catch (error) {
        errorDiv.textContent = '❌ Usuario o contraseña inválidos';
        errorDiv.style.display = 'block';
    }
}

async function handleLogout() {
    if (confirm('¿Seguro que desea cerrar sesión?')) {
        await API.logout();
        currentUser = null;
        showLoginPage();
    }
}

function showLoginPage() {
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('mainApp').classList.remove('active');
}

function showMainApp() {
    document.getElementById('loginPage').classList.remove('active');
    document.getElementById('mainApp').classList.add('active');
    updateUserInfo();
    navigateTo('dashboard');
}

function updateUserInfo() {
    if (currentUser) {
        const userNameEl = document.querySelector('.user-name');
        const userRoleEl = document.querySelector('.user-role');
        if (userNameEl) userNameEl.textContent = currentUser.full_name || currentUser.username;
        if (userRoleEl) userRoleEl.textContent = currentUser.role || 'Usuario';
    }
}

// Verificar autenticación al cargar
window.addEventListener('DOMContentLoaded', initAuth);
