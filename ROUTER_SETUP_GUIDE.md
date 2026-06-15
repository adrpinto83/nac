# 🚀 Step-by-Step Router Configuration Guide

## Step 1: Connect to Router

### Option A: Using Winbox (GUI)
1. Download Winbox from mikrotik.com
2. Run Winbox
3. Click the address bar and enter: `192.168.88.1`
4. Double-click the router (MAC address will appear)
5. Leave username blank, password: `admin`
6. Click Connect

### Option B: Using SSH
```bash
ssh admin@192.168.88.1
# Password: admin
```

### Option C: Using Telnet
```bash
telnet 192.168.88.1
# Login: admin (no password needed)
```

---

## Step 2: Configure WiFi Network

**Via Winbox:**
1. Go to `Wireless`
2. Find `wlan1` interface
3. Right-click → Edit
4. Set these values:
   - **SSID**: `WiFiD1405`
   - **Mode**: `ap bridge`
   - **Band**: `2GHz (b/g/n)`
   - **Channel**: `6`
   - **TX Power**: `20`
   - **Security Profile**: Leave as default or create new with NO security

5. Click OK and apply

**Via Command Line:**
```
/interface wireless
set [find default-name=wlan1] ssid="WiFiD1405" mode=ap-bridge band=2ghz-b/g/n channel=6 tx-power=20

/interface wireless security-profiles
add name=open-profile authentication-types="" encryption=""
set [find default-name=wlan1] security=open-profile
```

---

## Step 3: Configure DHCP Server

**Via Winbox:**
1. Go to `IP → Pools`
2. Click `+ (Add New)`
3. Set:
   - **Name**: `dhcp_pool`
   - **Ranges**: `192.168.88.100-192.168.88.200`
4. Click OK

Now for DHCP Server:
1. Go to `IP → DHCP Server`
2. Click `+ (Add New)`
3. Set:
   - **Name**: `dhcp1`
   - **Interface**: `bridge1`
   - **Address Pool**: `dhcp_pool`
4. Click OK

---

## Step 4: Configure Firewall - Address Lists

**Via Winbox:**
1. Go to `IP → Firewall → Address Lists`
2. Click `+ (Add New)` for each:

**List 1: authenticated-users**
- **List**: `authenticated-users`
- **Address**: `0.0.0.0/0` (placeholder)
- **Comment**: `Users approved by NAC system`
- Click OK

**List 2: local-network**
- **List**: `local-network`
- **Address**: `192.168.88.0/24`
- **Comment**: `Local network`
- Click OK

**List 3: local-network (gateway)**
- **List**: `local-network`
- **Address**: `192.168.88.1`
- **Comment**: `Router gateway`
- Click OK

---

## Step 5: Configure NAT Rules

**Via Winbox:**
1. Go to `IP → Firewall → NAT`
2. Click `+ (Add New)` for each rule:

**Rule 1: HTTP Redirect to Splash Page**
- **Chain**: `dstnat`
- **Protocol**: `tcp`
- **Dst. Port**: `80`
- **In. Interface**: `bridge1`
- **Action**: `dst-nat`
- **To Addresses**: `192.168.88.5`
- **To Ports**: `8080`
- **Comment**: `Redirect HTTP to splash page`
- Click OK

**Rule 2: Allow DNS**
- **Chain**: `srcnat`
- **Protocol**: `udp`
- **Dst. Port**: `53`
- **Out. Interface**: `bridge1`
- **Action**: `masquerade`
- **Comment**: `DNS queries`
- Click OK

---

## Step 6: Configure Firewall Filter Rules

**Via Winbox:**
1. Go to `IP → Firewall → Filter Rules`
2. Click `+ (Add New)` for each rule (order matters!):

**Rule 1: Allow Input to Router**
- **Chain**: `input`
- **In. Interface**: `bridge1`
- **Dst. Address**: `192.168.88.1`
- **Protocol**: `tcp`
- **Dst. Port**: `8080`
- **Action**: `accept`
- **Comment**: `Allow traffic to NAC system`
- Click OK

**Rule 2: Allow Output from Router**
- **Chain**: `forward`
- **Src. Address List**: `local-network`
- **Action**: `accept`
- **Comment**: `Allow local network traffic`
- Click OK

**Rule 3: Allow Authenticated Users**
- **Chain**: `forward`
- **Src. Address List**: `authenticated-users`
- **Action**: `accept`
- **Comment**: `Allow authenticated users to internet`
- Click OK

**Rule 4: Allow DHCP**
- **Chain**: `forward`
- **Protocol**: `udp`
- **Dst. Port**: `67`
- **Action**: `accept`
- **Comment**: `Allow DHCP`
- Click OK

**Rule 5: Allow DNS**
- **Chain**: `forward`
- **Protocol**: `udp`
- **Dst. Port**: `53`
- **Action**: `accept`
- **Comment**: `Allow DNS queries`
- Click OK

**Rule 6: Drop Unauth Users** (LAST RULE - Important!)
- **Chain**: `forward`
- **Src. Address**: `192.168.88.0/24`
- **Action**: `drop`
- **Comment**: `Block unauthenticated users from internet`
- Click OK

---

## Step 7: Test the Configuration

### Test 1: Connect to WiFi
```bash
# On your phone or laptop:
1. Open WiFi settings
2. Search for "WiFiD1405"
3. Click to connect (no password needed)
4. Open browser and go to http://google.com
```

**Expected Result**: Browser automatically redirects to `http://192.168.88.5:8080/splash`

### Test 2: Register a User
```
1. Fill out the registration form with:
   - Username: testuser
   - Password: password123
   - Full Name: Test User
   - Email: test@example.com
   - Phone: +1234567890

2. Click "Register Now"
3. Should see: "Registration Successful! Pending approval..."
```

### Test 3: Admin Approval
```
1. Open http://192.168.88.5:8080/ in your admin browser
2. Login with: admin / admin123
3. Click "Pending Users" (should show count badge)
4. See "testuser" in the list
5. Click "✓ Approve"
```

### Test 4: Verify Internet Access
```
1. Go back to the device that registered
2. Open browser and go to http://google.com
3. Should now load Google (or your default search page)
4. Internet is working!
```

---

## Step 8: Monitor Connected Users

**To see who's connected:**
1. In Winbox, go to `IP → DHCP Server → Leases`
2. You'll see all devices with IPs assigned

**Example output:**
```
ADDRESS         MAC-ADDRESS       HOST-NAME     EXPIRES-AFTER
192.168.88.100  AA:BB:CC:DD:EE:01 john-phone    5h 59m 45s
192.168.88.101  AA:BB:CC:DD:EE:02 jane-laptop   5h 58m 30s
```

---

## Step 9: Add Approved Users to Firewall

**Manual Method (One-time):**
```bash
# SSH into router
ssh admin@192.168.88.1

# Add MAC address to whitelist:
/ip firewall address-list
add list=authenticated-users address=AA:BB:CC:DD:EE:01 comment="john-phone"
add list=authenticated-users address=AA:BB:CC:DD:EE:02 comment="jane-laptop"

# Verify:
print
```

**Automatic Method (Coming Soon):**
- NAC system will automatically sync approved users' MAC addresses
- No manual configuration needed

---

## Troubleshooting

### Problem: WiFi network doesn't appear
**Solution:**
- Check if wlan1 interface is running: `interface print`
- Ensure it's enabled (green dot in Winbox)
- Try changing channel from 6 to 1, 11

### Problem: Can't connect to WiFi
**Solution:**
- In Winbox, check if interface security is set correctly
- Try removing and re-adding the interface
- Reboot the router: `/system reboot`

### Problem: Connected but can't see splash page
**Solution:**
1. Check if NAC system is running on 192.168.88.5:8080
2. Verify NAT rules exist: `/ip firewall nat print`
3. Check firewall filter rules: `/ip firewall filter print`

### Problem: Can't access internet after approval
**Solution:**
1. Verify MAC address is in `authenticated-users` list
2. Check firewall rules order (drop rule should be last)
3. Verify routing table: `/ip route print`

### Problem: Can't see NAC dashboard
**Solution:**
1. Ping the NAC server: `ping 192.168.88.5`
2. Check if port 8080 is open: `telnet 192.168.88.5 8080`
3. Verify NAC is running: `docker ps` (if using Docker)

---

## Reset / Factory Reset

**WARNING: This will erase all configuration!**

```bash
/system reset-configuration no-defaults=yes
/system reboot
```

---

## Quick Reference Commands

```bash
# Show all wireless interfaces
/interface wireless print

# Show all firewall rules
/ip firewall filter print
/ip firewall nat print
/ip firewall address-list print

# Show DHCP leases (connected users)
/ip dhcp-server lease print

# Reboot router
/system reboot

# Show system info
/system print

# Show IP configuration
/ip address print
```

---

## Video Walkthrough

If you prefer a visual guide, watch this video:
(Link to YouTube tutorial)

---

**Setup Time**: ~15 minutes  
**Difficulty**: Intermediate  
**Support**: Contact admin@nac.local

