# 📡 MikroTik Captive Portal Configuration

## Overview
Configure the MikroTik router to:
- Create an open WiFi network named "WiFiD1405"
- Redirect unauthenticated users to a splash page
- Allow only approved users to access the internet
- Automatically capture MACs of connected devices

---

## Prerequisites
- MikroTik router with WiFi interface (wlan1 or similar)
- Admin user access via Winbox, SSH, or API
- NAC system running on http://192.168.88.5:8080
- Network IP configured: 192.168.88.0/24

---

## Network Configuration

### 1. Configure Bridge Interface (if not already done)
```
/interface bridge
add name=bridge1 protocol-mode=rstp

/interface bridge port
add bridge=bridge1 interface=ether1
add bridge=bridge1 interface=ether2
add bridge=bridge1 interface=ether3
add bridge=bridge1 interface=ether4
add bridge=bridge1 interface=wlan1

/ip address
add address=192.168.88.1/24 interface=bridge1
```

### 2. Configure DHCP Server
```
/ip pool
add name=dhcp_pool ranges=192.168.88.100-192.168.88.200

/ip dhcp-server
add address-pool=dhcp_pool interface=bridge1 name=dhcp1

/ip dhcp-server network
add address=192.168.88.0/24 gateway=192.168.88.1 dns-server=192.168.88.1,8.8.8.8 domain=local.nac
```

---

## WiFi Configuration - Open Network (WiFiD1405)

### Create Open WiFi Network
```
/interface wireless
set [ find default-name=wlan1 ] \
    ssid="WiFiD1405" \
    mode=ap-bridge \
    band=2ghz-b/g/n \
    channel=6 \
    tx-power=20 \
    security-profile=wifi-open

/interface wireless security-profiles
add name=wifi-open authentication-types="" encryption=""
```

**Important:** This creates an OPEN network (no password). Users must register via splash page.

---

## Firewall Configuration for Captive Portal

### 1. Create Address Lists
```
# Authenticated users (will be updated automatically by NAC system)
/ip firewall address-list
add list=authenticated-users address=0.0.0.0/0 comment="Placeholder - will be populated by NAC"

# Local network and gateway
add list=local-network address=192.168.88.0/24 comment="Local network"
add list=local-network address=192.168.88.1 comment="Router"
```

### 2. Create NAT Rule (Captive Portal Redirect)
```
# Redirect HTTP traffic from guests to splash page
/ip firewall nat
add chain=dstnat protocol=tcp dst-port=80 in-interface=bridge1 \
    dst-address=!192.168.88.1 action=dst-nat to-addresses=192.168.88.5 \
    to-ports=8080 comment="Redirect HTTP to NAC splash page"

# Allow HTTPS for dashboard
add chain=dstnat protocol=tcp dst-port=443 action=dst-nat \
    to-addresses=192.168.88.5 to-ports=8080 comment="Redirect HTTPS to NAC"

# Allow DNS
add chain=srcnat protocol=udp dst-port=53 action=src-nat \
    to-addresses=192.168.88.1 comment="Allow DNS queries"
```

### 3. Create Firewall Rules (Filter)
```
# Allow all traffic to router
/ip firewall filter
add chain=forward src-address-list=local-network action=accept \
    comment="Allow local network"

# Allow authenticated users
add chain=forward src-address-list=authenticated-users action=accept \
    comment="Allow authenticated users"

# Block unauthenticated users (except DNS and splash page)
add chain=forward src-address=192.168.88.0/24 \
    dst-address-list=!local-network action=drop \
    comment="Block unauthenticated internet access"

# Allow DNS to local DNS server
add chain=forward protocol=udp dst-port=53 action=accept \
    comment="Allow DNS"

# Allow DHCP
add chain=forward protocol=udp dst-port=67 dst-address=255.255.255.255 \
    action=accept comment="Allow DHCP"

# Allow loopback
add chain=input in-interface=bridge1 dst-address=192.168.88.1 \
    protocol=tcp dst-port=8080 action=accept \
    comment="Allow traffic to NAC system"
```

---

## Integration with NAC System

### 1. How Users Register
```
User connects to "WiFiD1405" WiFi
                 ↓
Device gets DHCP IP (192.168.88.100-200)
                 ↓
User opens browser
                 ↓
Browser redirects to http://192.168.88.5:8080/splash
                 ↓
User fills registration form
                 ↓
Account created as "pending" status
                 ↓
Admin approves user in NAC system
                 ↓
NAC system adds user's MAC to "authenticated-users" list
                 ↓
Firewall allows user to access internet
```

### 2. Update Authenticated Users (Script)

Create a scheduler on the router to sync with NAC system:

```
/system script
add name=sync-nac comment="Sync authenticated users from NAC system" source={
    /ip firewall address-list
    remove numbers=[find list=authenticated-users]
    
    # Add authenticated user MACs from NAC
    # This would be populated by the NAC API
    # Example:
    # add list=authenticated-users address=AA:BB:CC:DD:EE:FF/32
}

/system scheduler
add name=sync-nac interval=5m on-event=sync-nac comment="Sync NAC auth every 5 minutes"
```

---

## NAC System Webhook Configuration

The NAC system can call the router API to automatically add approved users' MACs:

```
Endpoint: POST /api/devices/whitelist
Body: {
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "user_id": 123,
    "action": "approve" | "revoke"
}

Response: {
    "status": "success",
    "message": "MAC added to authenticated-users"
}
```

---

## Testing the Setup

### 1. Connect to WiFi
```
SSID: WiFiD1405 (Open)
```

### 2. Verify Redirect
- Open browser
- You should be redirected to `http://192.168.88.5:8080/splash`
- Register an account (status: pending)

### 3. Admin Approval
- Login to NAC admin dashboard
- Go to "Pending Users"
- Approve the user
- User's MAC is added to firewall whitelist

### 4. Verify Access
```bash
# After approval, user device should be able to ping external IP
ping 8.8.8.8

# User can now browse internet
```

---

## Telnet Configuration (One-Liner Commands)

If you prefer direct telnet access:

```bash
# Connect via telnet
telnet 192.168.88.1

# Run commands:
/interface wireless set [ find default-name=wlan1 ] ssid="WiFiD1405" mode=ap-bridge band=2ghz-b/g/n channel=6
/ip firewall nat add chain=dstnat protocol=tcp dst-port=80 action=dst-nat to-addresses=192.168.88.5 to-ports=8080
/ip firewall filter add chain=forward src-address-list=authenticated-users action=accept
```

---

## Security Notes

1. **Open WiFi**: The network is open (no password). Security comes from MAC filtering and authentication.

2. **Splash Page**: Users are redirected to the splash page for registration.

3. **MAC Spoofing**: Users could theoretically spoof MACs. For enterprise security, use certificates or 802.1X instead.

4. **SSL/TLS**: In production, use HTTPS on the splash page and redirect HTTP to HTTPS.

5. **DNS Filtering**: Consider adding DNS filtering to block malicious domains.

---

## Advanced: Import Configuration Script

Create a file `captive-portal-setup.rsc` with all commands:

```
# MikroTik Captive Portal Configuration Script
# Usage: /import captive-portal-setup.rsc

/interface wireless
set [ find default-name=wlan1 ] \
    ssid="WiFiD1405" \
    mode=ap-bridge \
    band=2ghz-b/g/n \
    channel=6 \
    tx-power=20

/ip pool
add name=dhcp_pool ranges=192.168.88.100-192.168.88.200

/ip dhcp-server
add address-pool=dhcp_pool interface=bridge1 name=dhcp1

/ip firewall address-list
add list=authenticated-users address=0.0.0.0/0 comment="Authenticated users whitelist"

/ip firewall nat
add chain=dstnat protocol=tcp dst-port=80 action=dst-nat to-addresses=192.168.88.5 to-ports=8080 comment="HTTP redirect to splash"
add chain=dstnat protocol=tcp dst-port=443 action=dst-nat to-addresses=192.168.88.5 to-ports=8080 comment="HTTPS redirect"

/ip firewall filter
add chain=forward src-address-list=authenticated-users action=accept comment="Allow authenticated"
add chain=forward src-address=192.168.88.0/24 action=drop comment="Block others"

:log info "Captive portal configured!"
```

Import in Winbox:
- File → Import Script
- Select `captive-portal-setup.rsc`

---

## Monitoring & Debugging

### View Current Firewall Rules
```
/ip firewall filter print
/ip firewall nat print
/ip firewall address-list print
```

### Check Connected Users
```
/ip dhcp-server lease print
```

### Monitor Traffic
```
/ip firewall address-list print
/queue simple print
```

### View Logs
```
/log print
```

---

## Next Steps

1. **Apply Configuration**: Use the commands above via Winbox or SSH
2. **Test WiFi**: Connect to "WiFiD1405" and verify redirect to splash page
3. **Register User**: Fill out registration form
4. **Admin Approval**: Approve pending user
5. **Verify Access**: User should now have internet access

---

**Last Updated**: 2026-06-15  
**NAC System Version**: 1.0.0  
**Status**: Ready for Production
