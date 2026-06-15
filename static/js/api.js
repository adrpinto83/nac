/**
 * Cliente API para consumir endpoints del backend FastAPI
 */

const API = {
    baseURL: 'http://localhost:8080/api',
    token: null,

    async request(method, endpoint, data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || `Error ${response.status}`);
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Auth
    async login(username, password) {
        const data = await this.request('POST', '/auth/login', { username, password });
        this.token = data.access_token;
        localStorage.setItem('token', this.token);
        return data;
    },

    async logout() {
        this.token = null;
        localStorage.removeItem('token');
    },

    async getCurrentUser() {
        return this.request('GET', '/auth/me');
    },

    // Users
    async listUsers(skip = 0, limit = 50) {
        return this.request('GET', `/users/?skip=${skip}&limit=${limit}`);
    },

    async getUser(userId) {
        return this.request('GET', `/users/${userId}`);
    },

    async createUser(data) {
        return this.request('POST', '/users/', data);
    },

    async updateUser(userId, data) {
        return this.request('PUT', `/users/${userId}`, data);
    },

    async deleteUser(userId) {
        return this.request('DELETE', `/users/${userId}`);
    },

    async suspendUser(userId) {
        return this.request('POST', `/users/${userId}/suspend`);
    },

    async activateUser(userId) {
        return this.request('POST', `/users/${userId}/activate`);
    },

    // Devices
    async registerDevice(data) {
        return this.request('POST', '/devices/register', data);
    },

    async listDevices(skip = 0, limit = 50) {
        return this.request('GET', `/devices/?skip=${skip}&limit=${limit}`);
    },

    async getLiveDevices() {
        return this.request('GET', '/devices/live');
    },

    async blockDevice(deviceId) {
        return this.request('POST', `/devices/${deviceId}/block`);
    },

    async unblockDevice(deviceId) {
        return this.request('POST', `/devices/${deviceId}/unblock`);
    },

    async deleteDevice(deviceId) {
        return this.request('DELETE', `/devices/${deviceId}`);
    },

    // Dashboard
    async getMetrics() {
        return this.request('GET', '/dashboard/metrics');
    },

    async getTopDevices(limit = 5) {
        return this.request('GET', `/dashboard/top-devices?limit=${limit}`);
    },

    async getAlerts() {
        return this.request('GET', '/dashboard/alerts');
    },

    async getNetworkStats(hours = 24) {
        return this.request('GET', `/dashboard/network-stats?hours=${hours}`);
    },

    // Profiles
    async listProfiles() {
        return this.request('GET', '/profiles/');
    },

    async createProfile(data) {
        return this.request('POST', '/profiles/', data);
    },

    async updateProfile(profileId, data) {
        return this.request('PUT', `/profiles/${profileId}`, data);
    },

    // DNS
    async listDNSCategories() {
        return this.request('GET', '/dns/categories');
    },

    async createDNSCategory(data) {
        return this.request('POST', '/dns/categories', data);
    },

    async listDNSEntries(categoryId = null) {
        const url = categoryId ? `/dns/entries?category_id=${categoryId}` : '/dns/entries';
        return this.request('GET', url);
    },

    async createDNSEntry(data) {
        return this.request('POST', '/dns/entries', data);
    },

    async deleteDNSEntry(entryId) {
        return this.request('DELETE', `/dns/entries/${entryId}`);
    },
};

// Restaurar token al cargar
window.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        API.token = token;
    }
});
