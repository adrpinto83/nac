# 👥 Enhanced User Management System

## Overview

The NAC system now includes a comprehensive user and device management system that allows:
- Track multiple devices per user (laptops, phones, tablets, etc.)
- Store detailed user information (phone, department, position, company)
- Maintain device details (manufacturer, model, serial number, OS, etc.)
- Full user-device relationship management

---

## 📊 Database Schema

### Users Table (Enhanced)
```
id                INTEGER (PRIMARY KEY)
username          TEXT (UNIQUE) - Login username
full_name         TEXT - User's full name
email             TEXT (UNIQUE) - Email address
phone             TEXT - Phone number
department        TEXT - Department/Team
position          TEXT - Job position/title
company           TEXT - Company name
password_hash     TEXT - Hashed password
role              TEXT - admin/operator/user
is_active         BOOLEAN - Account status
last_login        TIMESTAMP - Last login time
created_at        TIMESTAMP - Creation date
updated_at        TIMESTAMP - Last update
```

### Devices Table (Enhanced)
```
id                INTEGER (PRIMARY KEY)
user_id           INTEGER (FOREIGN KEY) - Owner of device
mac_address       TEXT (UNIQUE) - MAC address
ip_address        TEXT - Current IP address
hostname          TEXT - Device hostname
device_type       TEXT - laptop/phone/tablet/desktop/etc
manufacturer      TEXT - Device manufacturer (Dell, Apple, Samsung, etc)
model             TEXT - Device model
serial_number     TEXT - Serial number
os_type           TEXT - Windows/macOS/Linux/Android/iOS
os_version        TEXT - OS version
status            TEXT - online/offline/suspended
last_seen         TIMESTAMP - Last activity
notes             TEXT - Additional notes
created_at        TIMESTAMP - Registration date
updated_at        TIMESTAMP - Last update
```

### Device Types Table
```
id                INTEGER (PRIMARY KEY)
name              TEXT (UNIQUE) - laptop, phone, tablet, etc
description       TEXT - Device type description
```

### Audit Log Table (Enhanced)
```
id                INTEGER (PRIMARY KEY)
user_id           INTEGER (FOREIGN KEY) - Who performed action
action            TEXT - create/update/delete/login
entity_type       TEXT - user/device
entity_id         INTEGER - ID of affected entity
details           TEXT - Action details
ip_address        TEXT - Requester IP
timestamp         TIMESTAMP - When action occurred
```

---

## 🔌 API Endpoints

### User Management

#### List All Users
```bash
GET /api/users/
Authorization: Bearer <token>

Response: Array of UserResponse
[
  {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "email": "admin@nac.local",
    "phone": "+1234567890",
    "department": "IT",
    "position": "System Administrator",
    "company": "Company Inc",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-06-15T12:00:00"
  }
]
```

#### Create New User
```bash
POST /api/users/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "username": "john.doe",
  "password": "secure_password123",
  "full_name": "John Doe",
  "email": "john.doe@company.com",
  "phone": "+1987654321",
  "department": "Sales",
  "position": "Sales Manager",
  "company": "Company Inc",
  "role": "operator"
}

Response: UserResponse (same structure as above)
```

#### Get User Detail (with Devices)
```bash
GET /api/users/{user_id}
Authorization: Bearer <token>

Response: UserDetailResponse
{
  "id": 1,
  "username": "john.doe",
  "full_name": "John Doe",
  "email": "john.doe@company.com",
  "phone": "+1987654321",
  "department": "Sales",
  "position": "Sales Manager",
  "company": "Company Inc",
  "role": "operator",
  "is_active": true,
  "created_at": "2026-06-15T12:00:00",
  "last_login": "2026-06-15T14:30:00",
  "device_count": 3,
  "devices": [
    {
      "id": 1,
      "mac_address": "AA:BB:CC:DD:EE:01",
      "ip_address": "192.168.1.100",
      "hostname": "john-laptop",
      "device_type": "laptop",
      "manufacturer": "Dell",
      "model": "XPS 15",
      "os_type": "Windows",
      "status": "online",
      "last_seen": "2026-06-15T14:30:00"
    },
    {
      "id": 2,
      "mac_address": "AA:BB:CC:DD:EE:02",
      "ip_address": "192.168.1.101",
      "hostname": "john-phone",
      "device_type": "smartphone",
      "manufacturer": "Apple",
      "model": "iPhone 14 Pro",
      "os_type": "iOS",
      "status": "online",
      "last_seen": "2026-06-15T14:25:00"
    }
  ]
}
```

#### Update User Information
```bash
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

Request: (All fields optional)
{
  "full_name": "John Updated Doe",
  "phone": "+1555555555",
  "department": "Marketing",
  "position": "Senior Manager",
  "company": "New Company"
}

Response: UserResponse
```

#### Delete User (and all devices)
```bash
DELETE /api/users/{user_id}
Authorization: Bearer <token>

Response:
{
  "message": "User deleted successfully"
}
```

#### Get User's Devices
```bash
GET /api/users/{user_id}/devices
Authorization: Bearer <token>

Response: Array of DeviceResponse
```

---

### Device Management

#### List All Devices
```bash
GET /api/devices/
Authorization: Bearer <token>

Response: Array of DeviceResponse
```

#### Register New Device for User
```bash
POST /api/devices/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "user_id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "hostname": "john-laptop",
  "device_type": "laptop",
  "manufacturer": "Dell",
  "model": "XPS 15",
  "serial_number": "SERIAL123456",
  "os_type": "Windows",
  "os_version": "11 Pro",
  "notes": "Company issued laptop"
}

Response: DeviceResponse
```

#### Get Device Details
```bash
GET /api/devices/{device_id}
Authorization: Bearer <token>

Response: DeviceResponse
```

#### Update Device Information
```bash
PUT /api/devices/{device_id}
Authorization: Bearer <token>
Content-Type: application/json

Request: (All fields optional)
{
  "hostname": "updated-hostname",
  "device_type": "laptop",
  "manufacturer": "Apple",
  "model": "MacBook Pro",
  "status": "online"
}

Response: DeviceResponse
```

#### Delete Device
```bash
DELETE /api/devices/{device_id}
Authorization: Bearer <token>

Response:
{
  "message": "Device deleted successfully"
}
```

#### Get All Devices for User
```bash
GET /api/devices/user/{user_id}/devices
Authorization: Bearer <token>

Response: Array of DeviceResponse
```

#### Get Device by MAC Address
```bash
GET /api/devices/by-mac/{mac_address}
Authorization: Bearer <token>

Response: DeviceResponse
```

---

## 📋 Device Types

Predefined device types available:
- `laptop` - Laptop Computer
- `desktop` - Desktop Computer
- `smartphone` - Mobile Phone
- `tablet` - Tablet Device
- `printer` - Network Printer
- `router` - Network Router
- `other` - Other Device

---

## 💻 Usage Examples

### Example 1: Create User with Devices
```bash
#!/bin/bash

# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# 2. Create user
USER=$(curl -s -X POST http://localhost:8080/api/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice.smith",
    "password": "secure123",
    "full_name": "Alice Smith",
    "email": "alice@company.com",
    "phone": "+1555123456",
    "department": "Engineering",
    "position": "Senior Engineer",
    "company": "Tech Corp"
  }')

USER_ID=$(echo $USER | jq -r '.id')

# 3. Register user's laptop
curl -s -X POST http://localhost:8080/api/devices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"mac_address\": \"AA:BB:CC:DD:EE:01\",
    \"hostname\": \"alice-laptop\",
    \"device_type\": \"laptop\",
    \"manufacturer\": \"Lenovo\",
    \"model\": \"ThinkPad X1\",
    \"serial_number\": \"LP001\",
    \"os_type\": \"Linux\",
    \"os_version\": \"Ubuntu 22.04\"
  }"

# 4. Register user's phone
curl -s -X POST http://localhost:8080/api/devices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"mac_address\": \"AA:BB:CC:DD:EE:02\",
    \"hostname\": \"alice-phone\",
    \"device_type\": \"smartphone\",
    \"manufacturer\": \"Samsung\",
    \"model\": \"Galaxy S23\",
    \"serial_number\": \"PH001\",
    \"os_type\": \"Android\",
    \"os_version\": \"13\"
  }"

# 5. Get user with all devices
curl -s -X GET http://localhost:8080/api/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Example 2: Update Device Information
```bash
TOKEN="your_token_here"

curl -s -X PUT http://localhost:8080/api/devices/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "new-hostname",
    "status": "offline",
    "notes": "Device transferred to new user"
  }' | jq .
```

### Example 3: Search Device by MAC
```bash
TOKEN="your_token_here"
MAC="AA:BB:CC:DD:EE:FF"

curl -s -X GET http://localhost:8080/api/devices/by-mac/$MAC \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 🔒 Security Considerations

1. **Device Association**: Devices are tied to users - deleting a user also deletes all associated devices
2. **MAC Address Uniqueness**: Each device must have a unique MAC address
3. **Audit Trail**: All device operations are logged with user, action, and timestamp
4. **Access Control**: Only authenticated users can manage devices
5. **Data Validation**: All inputs are validated using Pydantic models

---

## 📈 Data Insights You Can Track

### Per User:
- Number of devices owned
- Device types (laptop, phone, etc.)
- Active vs inactive devices
- Last login time
- Department/team organization
- Contact information
- Position/role

### Per Device:
- Device owner
- Hardware specifications (manufacturer, model)
- OS type and version
- Current status (online/offline)
- Last activity time
- Network information (IP, MAC)
- Serial number (for inventory)
- Custom notes

### Analytics Possible:
- Devices per user/department
- Device type distribution
- Most common manufacturers/models
- Offline device tracking
- Device inventory management
- User activity patterns
- Device lifecycle tracking

---

## 🚀 Future Enhancements

```
□ Device groups/categories
□ Device location tracking
□ Battery status monitoring (mobile)
□ Network bandwidth per device
□ Antivirus/security status
□ Software inventory per device
□ Hardware upgrade tracking
□ Device expense tracking
□ Export to CSV/JSON
□ Advanced filtering and search
□ Device monitoring alerts
□ Mobile app for device registration
```

---

**This system provides enterprise-grade user and device management capabilities!** 🎯
