# 🔐 API Authentication Guide

## Features Added

✅ **SQLite Database** - Users, Devices, and Audit Log tables
✅ **JWT Authentication** - Secure token-based authentication
✅ **Password Hashing** - Bcrypt for secure password storage
✅ **User Management** - CRUD operations for users
✅ **Device Management** - CRUD operations for devices
✅ **Protected Endpoints** - All endpoints require authentication token

---

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Devices Table
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    hostname TEXT,
    status TEXT DEFAULT 'offline',
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Audit Log Table
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
```

---

## 🔓 Default Credentials

```
Username: admin
Password: admin123
Role: admin
```

---

## 📡 API Endpoints

### 1. Authentication

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "admin",
  "full_name": "Administrator",
  "email": "admin@nac.local",
  "role": "admin",
  "is_active": true
}
```

#### Logout
```bash
POST /api/auth/logout
Authorization: Bearer <token>

Response:
{
  "message": "Logged out successfully"
}
```

---

### 2. Users Management

#### List All Users
```bash
GET /api/users/
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "email": "admin@nac.local",
    "role": "admin",
    "is_active": true
  }
]
```

#### Create New User
```bash
POST /api/users/
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "operator1",
  "password": "secure_password123",
  "full_name": "Operator One",
  "email": "operator1@nac.local",
  "role": "operator"
}

Response:
{
  "id": 2,
  "username": "operator1",
  "full_name": "Operator One",
  "email": "operator1@nac.local",
  "role": "operator",
  "is_active": true
}
```

#### Get User by ID
```bash
GET /api/users/{user_id}
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "admin",
  "full_name": "Administrator",
  "email": "admin@nac.local",
  "role": "admin",
  "is_active": true
}
```

#### Delete User
```bash
DELETE /api/users/{user_id}
Authorization: Bearer <token>

Response:
{
  "message": "User deleted"
}
```

---

### 3. Devices Management

#### List All Devices
```bash
GET /api/devices/
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "hostname": "user-laptop",
    "status": "online",
    "last_seen": "2026-06-15 12:30:45"
  }
]
```

#### Get Live Devices
```bash
GET /api/devices/live
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "ip_address": "192.168.88.10",
    "hostname": "user-laptop",
    "status": "online",
    "last_seen": "2026-06-15 12:30:45"
  }
]
```

#### Register Device
```bash
POST /api/devices/
Authorization: Bearer <token>
Content-Type: application/json

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "hostname": "user-laptop",
  "device_type": "laptop"
}

Response:
{
  "id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "ip_address": "",
  "hostname": "user-laptop",
  "status": "online",
  "last_seen": ""
}
```

#### Delete Device
```bash
DELETE /api/devices/{device_id}
Authorization: Bearer <token>

Response:
{
  "message": "Device deleted"
}
```

---

## 🛡️ Authentication Flow

### 1. Login
```
Client → POST /api/auth/login → Server
Server → Hash password + Compare → Database
Server → Generate JWT token → Client
Client → Store token (localStorage/sessionStorage)
```

### 2. Protected Request
```
Client → GET /api/users/ with "Authorization: Bearer <token>"
Server → Decode JWT token
Server → Verify token signature and expiration
Server → Execute request if valid
Server → Return 401 if token invalid/expired
```

### 3. Token Expiration
```
Token expires after: 30 minutes (default)
After expiration: User must login again
Token refresh: Not implemented yet (use new login)
```

---

## 🔑 Token Structure (JWT)

The token contains the following claims:
```json
{
  "sub": "admin",           // Subject (username)
  "exp": 1687000000,        // Expiration timestamp
  "iat": 1686999000         // Issued at timestamp
}
```

---

## 📦 Dependencies Used

- **FastAPI** - Web framework
- **aiosqlite** - Async SQLite
- **passlib[bcrypt]** - Password hashing
- **python-jose[cryptography]** - JWT handling
- **pydantic** - Data validation

---

## 🚀 Usage Examples

### Example 1: Login and Get User Info
```python
import requests

# Login
response = requests.post(
    "https://nac-production.up.railway.app/api/auth/login",
    json={
        "username": "admin",
        "password": "admin123"
    }
)

token = response.json()["access_token"]

# Get user info
response = requests.get(
    "https://nac-production.up.railway.app/api/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)

print(response.json())
```

### Example 2: Create New User
```python
import requests

token = "your_token_here"

response = requests.post(
    "https://nac-production.up.railway.app/api/users/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "username": "newuser",
        "password": "secure123",
        "full_name": "New User",
        "email": "newuser@nac.local",
        "role": "operator"
    }
)

print(response.json())
```

### Example 3: Register Device
```python
import requests

token = "your_token_here"

response = requests.post(
    "https://nac-production.up.railway.app/api/devices/",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "hostname": "user-device",
        "device_type": "phone"
    }
)

print(response.json())
```

---

## ⚠️ Security Notes

1. **Change Default Password**: Change admin password in production
2. **Use HTTPS**: Always use HTTPS in production
3. **Secure Token Storage**: Never store tokens in cookies without HttpOnly flag
4. **Token Expiration**: Implement token refresh mechanism for long sessions
5. **Rate Limiting**: Add rate limiting to login endpoint
6. **Input Validation**: All inputs are validated using Pydantic

---

## 🔄 Next Steps

1. Configure environment variables:
   ```
   SECRET_KEY=your-secret-key-here
   ```

2. Implement token refresh mechanism

3. Add role-based access control (RBAC)

4. Implement password change endpoint

5. Add email verification for new users

6. Implement audit logging for all actions

---

## 📞 Testing the API

Use any of these tools:
- **curl**: `curl -H "Authorization: Bearer <token>" https://nac-production.up.railway.app/api/users/`
- **Postman**: Import the endpoints
- **Thunder Client**: VS Code extension
- **Python requests**: See examples above
- **Frontend**: See /api/auth/me endpoint for JavaScript example

---

**¡API de autenticación lista para usar!** 🚀
