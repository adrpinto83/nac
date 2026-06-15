# 🚀 WiFi Captive Portal - Quick Start Guide

## What You've Built

A complete WiFi network access control system with:
- **Open WiFi network**: `WiFiD1405` (no password)
- **Splash page**: Public registration at `/splash`
- **User approval**: Admin dashboard controls who gets internet
- **Auto-sync**: Approved users automatically added to router whitelist
- **Fully automated**: Zero manual configuration after setup

---

## 🎯 Quick Summary

```
User connects to WiFiD1405
         ↓
Redirected to splash page
         ↓
Fills registration form
         ↓
Account created (pending approval)
         ↓
Admin approves in NAC dashboard
         ↓
User's device MAC automatically whitelisted
         ↓
User gets internet access ✓
```

---

## ⚡ 5-Minute Setup

### Step 1: Configure Router WiFi
```bash
# SSH into router:
ssh admin@192.168.88.1

# Copy this entire block and paste at once:
/interface wireless set [find default-name=wlan1] ssid="WiFiD1405" mode=ap-bridge band=2ghz-b/g/n channel=6 tx-power=20
/ip pool add name=dhcp_pool ranges=192.168.88.100-192.168.88.200
/ip dhcp-server add address-pool=dhcp_pool interface=bridge1 name=dhcp1
/ip firewall address-list add list=authenticated-users address=0.0.0.0/0 comment="NAC system whitelist"
/ip firewall nat add chain=dstnat protocol=tcp dst-port=80 action=dst-nat to-addresses=192.168.88.5 to-ports=8080 comment="Splash redirect"
/ip firewall filter add chain=input in-interface=bridge1 dst-address=192.168.88.1 protocol=tcp dst-port=8080 action=accept
/ip firewall filter add chain=forward src-address-list=authenticated-users action=accept
/ip firewall filter add chain=forward protocol=udp dst-port=53 action=accept
/ip firewall filter add chain=forward src-address=192.168.88.0/24 action=drop
```

### Step 2: No More Configuration Needed!

The NAC system handles everything automatically.

---

## 🔑 Key Features

### 1. **Public Registration Page**
- URL: `http://192.168.88.5:8080/splash`
- Users fill: Username, Password, Name, Email, Phone
- Account created as "pending"

### 2. **Admin Approval Dashboard**
- URL: `http://192.168.88.5:8080/`
- Login: `admin` / `admin123`
- Go to "Pending Users" tab
- Approve or reject each user
- **Auto-sync**: Approved users' MACs added to router whitelist

### 3. **Automatic Whitelist Sync**
- When you approve a user in NAC → MAC is added to router
- When user registers a device → Device can be whitelisted
- Manual sync available: `POST /api/router/sync-approved-users`

---

## 📱 User Flow

### For End Users:
```
1. Connect to WiFiD1405 (open network)
2. Open browser → Redirected to splash page
3. Fill registration form
4. See "Pending approval" message
5. Wait for admin approval (real-time)
6. After approval → Internet works!
```

### For Admins:
```
1. Go to NAC dashboard: http://192.168.88.5:8080/
2. Click "Pending Users" in sidebar
3. Review pending registrations
4. Click ✓ Approve or ✗ Reject
5. Done! MAC is automatically added to router whitelist
6. User now has internet access
```

---

## 🔌 API Endpoints

### Public Endpoints
```
POST /api/auth/register
  - Public user registration
  - No token required
  - Creates user in "pending" status

GET /splash
  - Splash page for WiFi registration
  - Served to unauthenticated users
```

### Admin Endpoints (Token Required)
```
GET /api/auth/pending-users
  - List all pending users
  - Returns count and details

POST /api/auth/approve-user/{user_id}
  - Approve a pending user
  - Auto-syncs MAC to router

POST /api/auth/reject-user/{user_id}
  - Reject a pending user
  - Removes from whitelist

POST /api/router/sync-approved-users
  - Manually sync all approved users
  - Useful for troubleshooting

POST /api/router/whitelist-user
  - Manually add MAC to router

POST /api/router/remove-user
  - Manually remove MAC from router

GET /api/router/authenticated-users
  - View current authenticated users on router
```

---

## 🧪 Testing

### Test 1: Connect to WiFi
```
Device: Phone/Laptop
WiFi: WiFiD1405 (no password)
Browser: Opens automatically → Redirects to splash page
```

### Test 2: Register a User
```
Fill form:
- Username: testuser
- Password: test123
- Name: Test User
- Email: test@example.com
- Phone: +1234567890

Result: "Registration successful! Pending approval..."
```

### Test 3: Approve User
```
1. NAC Dashboard: http://192.168.88.5:8080/
2. Login: admin/admin123
3. Click Pending Users (see badge with count)
4. Click ✓ Approve next to testuser
5. See: "User approved!"
```

### Test 4: Verify Internet Access
```
1. Go back to device
2. Open browser
3. Try visiting google.com
4. Should load successfully ✓
```

---

## 🔧 Troubleshooting

### Problem: Can't see splash page
**Solution:**
1. Check NAC is running: `http://192.168.88.5:8080/`
2. Check router NAT rule: `/ip firewall nat print`
3. Verify DNS: `nslookup 192.168.88.5`

### Problem: User approved but no internet
**Solution:**
1. Check MAC is in router: `GET /api/router/authenticated-users`
2. Manually sync: `POST /api/router/sync-approved-users`
3. Check device MAC: `ipconfig /all` (Windows) or `ifconfig` (Mac/Linux)

### Problem: User can't register
**Solution:**
1. Check username doesn't already exist
2. Check email format
3. Verify splash page loads: `http://192.168.88.5:8080/splash`

### Problem: Router config not working
**Solution:**
1. Check firewall rules order (drop rule must be last)
2. Verify interface is enabled
3. Check routing: `/ip route print`

---

## 📊 Monitoring

### See Connected Users
```bash
# SSH to router:
/ip dhcp-server lease print

# Shows:
192.168.88.100  AA:BB:CC:DD:EE:01  john-phone
192.168.88.101  AA:BB:CC:DD:EE:02  jane-laptop
192.168.88.102  AA:BB:CC:DD:EE:03  bob-laptop
```

### See Authenticated Users (Whitelisted)
```bash
# API call:
GET /api/router/authenticated-users
Authorization: Bearer <admin-token>

# Returns list of MACs in authenticated-users list
```

### View NAC Logs
```bash
# In NAC dashboard:
1. Go to any page
2. Check browser console (F12)
3. See API calls and responses
```

---

## 🛡️ Security Notes

1. **Open WiFi**: The network is open (no password) for convenience
   - Security comes from MAC filtering in firewall
   - Consider using WPA2 + registration for higher security

2. **Admin Access**: Keep `admin/admin123` secure
   - Change password immediately: Update in NAC dashboard

3. **MAC Spoofing**: Users could spoof MAC addresses
   - For enterprise: Use 802.1X or certificate authentication
   - For small networks: MAC filtering is adequate

4. **HTTPS**: Use HTTP for demo, HTTPS for production
   - Deploy behind HTTPS proxy (nginx, etc.)

---

## 🚀 Advanced Configuration

### Auto-Approve Selected Users
```python
# Modify auth.py approve_user endpoint
# Add condition to auto-approve certain domains:
if email.endswith("@company.com"):
    await approve_user_auto(user_id)
```

### Email Notifications
```python
# Add to approve_user endpoint:
await send_email(
    user.email,
    "Account Approved!",
    "Your WiFi access has been approved. You can now connect."
)
```

### Time-Based Access
```python
# Add to firewall rules:
/ip firewall filter add \
    chain=forward \
    src-address-list=authenticated-users \
    time=08:00-18:00 \
    action=accept
```

---

## 📋 Checklist

- [ ] Router WiFi configured as `WiFiD1405`
- [ ] DHCP pool: `192.168.88.100-200`
- [ ] Firewall rules added (5 rules minimum)
- [ ] NAT rule for HTTP redirect
- [ ] NAC system running on `192.168.88.5:8080`
- [ ] Can see splash page when connecting
- [ ] Can register a user
- [ ] Can approve user in admin dashboard
- [ ] Approved user can access internet
- [ ] Admin password changed (if in production)

---

## 📞 Support

**NAC System Issues:**
- Check `http://192.168.88.5:8080/`
- Check browser console (F12)
- Check server logs

**Router Issues:**
- Check `/ip firewall filter print` rules order
- Check `/ip firewall nat print` rules
- SSH: `ssh admin@192.168.88.1`

**WiFi Issues:**
- Check wireless interface: `/interface wireless print`
- Try different channel (6, 11, etc.)
- Check TX power

---

## 📦 What's Deployed

- **Frontend**: Modern React-like single-page app
- **Backend**: FastAPI with JWT authentication
- **Database**: SQLite with user/device tracking
- **Router Integration**: MikroTik API sync
- **Hosting**: Railway.app (production)
- **Code**: GitHub repository with full docs

---

## 🎓 Learn More

- Full Technical Docs: `ROUTER_CAPTIVE_PORTAL_CONFIG.md`
- Step-by-Step Guide: `ROUTER_SETUP_GUIDE.md`
- API Documentation: `API_AUTHENTICATION.md`
- User Management: `ENHANCED_USER_MANAGEMENT.md`

---

**Status**: ✅ Ready for Production
**Version**: 1.0.0
**Last Updated**: 2026-06-15

