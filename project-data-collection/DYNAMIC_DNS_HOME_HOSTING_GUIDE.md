# Dynamic DNS for Self-Hosting at Home

## Overview

Dynamic IP addresses change periodically (daily, weekly, or when your modem resets). Dynamic DNS (DDNS) automatically updates your DNS records to point to your current IP address.

---

## Quick Comparison: DDNS Providers

| Provider | Free Tier | Custom Domain Support | Update Method | API Quality | Recommended For |
|----------|-----------|----------------------|---------------|-------------|-----------------|
| **Cloudflare** | ✅ Yes (full DNS) | ✅ Yes | API | ⭐⭐⭐⭐⭐ Excellent | **Best overall** |
| **DuckDNS** | ✅ Yes | ❌ Subdomain only | API/URL | ⭐⭐⭐⭐ Good | Simple setup |
| **No-IP** | ✅ 3 hostnames | ✅ Yes (paid) | API/Client | ⭐⭐⭐ OK | Legacy systems |
| **Dynu** | ✅ 4 hostnames | ✅ Yes | API | ⭐⭐⭐⭐ Good | Free custom domains |
| **FreeDNS** | ✅ Unlimited | ✅ Yes | API/URL | ⭐⭐⭐ OK | Many subdomains |

**Recommendation**: Use **Cloudflare** if you own a domain, otherwise **DuckDNS** for simplicity.

---

## Option 1: Cloudflare (RECOMMENDED)

### Why Cloudflare?

✅ **Free forever** (no limitations)
✅ **Use your own domain** (e.g., `combos.yourdomain.com`)
✅ **Fast propagation** (<5 seconds)
✅ **Excellent API** (well-documented)
✅ **Additional features**: CDN, DDoS protection, SSL certificates
✅ **No client software needed** (just a script)

### Prerequisites

1. Own a domain (e.g., from Namecheap, Google Domains, etc.)
2. Point domain nameservers to Cloudflare
3. Get Cloudflare API token

### Step 1: Set Up Cloudflare

```bash
# 1. Sign up at cloudflare.com
# 2. Add your domain
# 3. Change nameservers at your domain registrar to Cloudflare's
# 4. Create API token:
#    - Go to: My Profile → API Tokens → Create Token
#    - Use template: "Edit zone DNS"
#    - Zone Resources: Include → Specific zone → yourdomain.com
#    - Copy the token
```

### Step 2: Install DDNS Updater Script

**Option A: Using `ddclient` (Most Popular)**

```bash
# Install ddclient
sudo apt update
sudo apt install ddclient libio-socket-ssl-perl libio-socket-inet6-perl

# Configure
sudo nano /etc/ddclient.conf
```

**ddclient.conf for Cloudflare:**

```conf
# ddclient configuration for Cloudflare
daemon=300                              # Check IP every 5 minutes
syslog=yes                              # Log to syslog
pid=/var/run/ddclient.pid              # PID file location
ssl=yes                                 # Use SSL

# Use Cloudflare
use=web, web=checkip.dyndns.org        # Get public IP from this service

# Cloudflare settings
protocol=cloudflare
zone=yourdomain.com                     # Your domain
ttl=120                                 # DNS TTL (2 minutes)
login=token                             # Use API token authentication
password=YOUR_CLOUDFLARE_API_TOKEN      # Your API token from step 1

# Hostname to update (can list multiple)
combos.yourdomain.com,api.yourdomain.com
```

**Start ddclient:**

```bash
# Enable and start service
sudo systemctl enable ddclient
sudo systemctl start ddclient

# Check status
sudo systemctl status ddclient

# Check logs
sudo journalctl -u ddclient -f

# Force update (test)
sudo ddclient -daemon=0 -debug -verbose -noquiet
```

**Option B: Custom Python Script (More Control)**

```python
#!/usr/bin/env python3
"""
Cloudflare DDNS Updater
Updates DNS A record when public IP changes
"""

import requests
import json
import logging
from pathlib import Path

# Configuration
CLOUDFLARE_API_TOKEN = "YOUR_API_TOKEN_HERE"
ZONE_ID = "YOUR_ZONE_ID"  # Found in Cloudflare dashboard
RECORD_NAME = "combos.yourdomain.com"
RECORD_TYPE = "A"
TTL = 120  # 2 minutes

# Cache file to store last known IP
CACHE_FILE = Path.home() / ".ddns_last_ip"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_public_ip():
    """Get current public IP address"""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        return response.json()["ip"]
    except Exception as e:
        logger.error(f"Failed to get public IP: {e}")
        return None


def get_cached_ip():
    """Get last known IP from cache"""
    if CACHE_FILE.exists():
        return CACHE_FILE.read_text().strip()
    return None


def save_cached_ip(ip):
    """Save current IP to cache"""
    CACHE_FILE.write_text(ip)


def get_dns_record():
    """Get current DNS record from Cloudflare"""
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "type": RECORD_TYPE,
        "name": RECORD_NAME
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    if data["success"] and data["result"]:
        return data["result"][0]
    return None


def update_dns_record(record_id, new_ip):
    """Update DNS record with new IP"""
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": RECORD_TYPE,
        "name": RECORD_NAME,
        "content": new_ip,
        "ttl": TTL,
        "proxied": False  # Set to True for Cloudflare proxy (DDoS protection)
    }

    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    if result["success"]:
        logger.info(f"✅ DNS updated: {RECORD_NAME} → {new_ip}")
        return True
    else:
        logger.error(f"❌ DNS update failed: {result}")
        return False


def create_dns_record(ip):
    """Create new DNS record"""
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": RECORD_TYPE,
        "name": RECORD_NAME,
        "content": ip,
        "ttl": TTL,
        "proxied": False
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    if result["success"]:
        logger.info(f"✅ DNS record created: {RECORD_NAME} → {ip}")
        return True
    else:
        logger.error(f"❌ DNS creation failed: {result}")
        return False


def main():
    """Main DDNS update logic"""
    # Get current public IP
    current_ip = get_public_ip()
    if not current_ip:
        logger.error("Could not determine public IP")
        return

    # Check if IP has changed
    cached_ip = get_cached_ip()
    if current_ip == cached_ip:
        logger.info(f"IP unchanged: {current_ip}")
        return

    logger.info(f"IP changed: {cached_ip} → {current_ip}")

    # Get existing DNS record
    record = get_dns_record()

    if record:
        # Update existing record
        if update_dns_record(record["id"], current_ip):
            save_cached_ip(current_ip)
    else:
        # Create new record
        if create_dns_record(current_ip):
            save_cached_ip(current_ip)


if __name__ == "__main__":
    main()
```

**Save as:** `/home/maxwell/scripts/cloudflare_ddns.py`

**Make executable:**

```bash
chmod +x /home/maxwell/scripts/cloudflare_ddns.py
```

**Install dependencies:**

```bash
pip install requests
```

**Test it:**

```bash
python3 /home/maxwell/scripts/cloudflare_ddns.py
```

### Step 3: Automate with Cron

```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * /usr/bin/python3 /home/maxwell/scripts/cloudflare_ddns.py >> /var/log/ddns.log 2>&1
```

**Or use systemd timer (more reliable):**

**Create service file:**

```bash
sudo nano /etc/systemd/system/cloudflare-ddns.service
```

```ini
[Unit]
Description=Cloudflare DDNS Updater
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/maxwell/scripts/cloudflare_ddns.py
User=maxwell
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Create timer file:**

```bash
sudo nano /etc/systemd/system/cloudflare-ddns.timer
```

```ini
[Unit]
Description=Run Cloudflare DDNS updater every 5 minutes
Requires=cloudflare-ddns.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
AccuracySec=1s

[Install]
WantedBy=timers.target
```

**Enable and start timer:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflare-ddns.timer
sudo systemctl start cloudflare-ddns.timer

# Check status
sudo systemctl status cloudflare-ddns.timer
sudo systemctl list-timers --all | grep cloudflare

# View logs
sudo journalctl -u cloudflare-ddns.service -f
```

---

## Option 2: DuckDNS (Simplest)

### Why DuckDNS?

✅ **100% free** (forever)
✅ **No registration required** (just email)
✅ **Super simple setup** (one-line script)
✅ **Good for testing** or if you don't own a domain

❌ **Subdomain only** (e.g., `mycombos.duckdns.org`)
❌ **No custom domain** support

### Step 1: Get DuckDNS Subdomain

```bash
# 1. Go to https://www.duckdns.org/
# 2. Sign in with Google/GitHub/etc.
# 3. Create a subdomain (e.g., "mycombos")
# 4. Copy your token
```

### Step 2: Install Update Script

**One-liner updater:**

```bash
# Create script
mkdir -p ~/duckdns
cd ~/duckdns
nano duck.sh
```

**duck.sh:**

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=mycombos&token=YOUR_TOKEN_HERE&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

**Make executable:**

```bash
chmod +x duck.sh
```

**Test it:**

```bash
./duck.sh
cat duck.log  # Should say "OK"
```

### Step 3: Automate

```bash
# Add to crontab
crontab -e

# Update every 5 minutes
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

**Your ML API will be available at:**
```
https://mycombos.duckdns.org
```

---

## Option 3: No-IP (Legacy but Widely Supported)

### Setup

```bash
# Install No-IP client
cd /tmp
wget https://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xzf noip-duc-linux.tar.gz
cd noip-2.1.9-1/
make
sudo make install

# Configure
sudo noip2 -C

# Start
sudo noip2

# Check status
sudo noip2 -S
```

---

## Router-Based DDNS (Alternative)

Many routers have built-in DDNS support. This is the **easiest** option if available.

### Supported Routers

✅ **ASUS** → Cloudflare, No-IP, DynDNS, ASUS DDNS
✅ **TP-Link** → No-IP, DynDNS
✅ **Netgear** → No-IP, DynDNS
✅ **Synology** → Many providers
✅ **pfSense/OPNsense** → All major providers

### How to Enable

1. Log into router admin panel
2. Find "DDNS" or "Dynamic DNS" settings
3. Choose provider (e.g., Cloudflare, No-IP)
4. Enter credentials/token
5. Save and enable

**Advantages**:
- No scripts needed on server
- Works even if server is down
- Updates immediately when IP changes

**Disadvantages**:
- Not all routers support all providers
- Less control over update frequency

---

## Complete Home Hosting Setup

### Network Configuration

```
Internet (Dynamic IP)
    ↓
Router (Port Forwarding)
    ↓ Port 80, 443
Home Server (Your ML API)
```

### Step 1: Configure Port Forwarding

**Forward these ports to your server:**

| Port | Protocol | Service | Required? |
|------|----------|---------|-----------|
| 80 | TCP | HTTP | ✅ Yes (for Let's Encrypt) |
| 443 | TCP | HTTPS | ✅ Yes (encrypted API) |
| 22 | TCP | SSH | ⚠️ Optional (change to non-standard port) |

**How to set up (example for common routers):**

```
1. Find your server's local IP: ip addr show
   Example: 192.168.1.100

2. Log into router (usually 192.168.1.1 or 192.168.0.1)

3. Find "Port Forwarding" or "Virtual Server" settings

4. Add rules:
   - External Port: 80 → Internal IP: 192.168.1.100, Port: 80
   - External Port: 443 → Internal IP: 192.168.1.100, Port: 443

5. Save and reboot router
```

### Step 2: Set Static Local IP (Important!)

**Option A: Router DHCP Reservation**
```
1. Router admin → DHCP Settings
2. Find your server's MAC address
3. Reserve IP (e.g., 192.168.1.100)
```

**Option B: Static IP on Server**

```bash
# For Ubuntu/Debian with netplan
sudo nano /etc/netplan/01-netcfg.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:  # or enp0s3, check with 'ip link'
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

```bash
sudo netplan apply
```

### Step 3: Install Reverse Proxy (Nginx)

```bash
sudo apt update
sudo apt install nginx
```

**Basic Nginx config:**

```nginx
# /etc/nginx/sites-available/combos
server {
    listen 80;
    server_name combos.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;  # Your FastAPI app
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/combos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: Get SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (automatic Nginx config)
sudo certbot --nginx -d combos.yourdomain.com

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

**Your Nginx config will be auto-updated to:**

```nginx
server {
    listen 443 ssl;
    server_name combos.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/combos.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/combos.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        # ... proxy settings ...
    }
}

server {
    listen 80;
    server_name combos.yourdomain.com;
    return 301 https://$server_name$request_uri;  # Redirect to HTTPS
}
```

---

## Monitoring and Reliability

### 1. Monitor IP Changes

**Script to get notified:**

```python
#!/usr/bin/env python3
"""
IP Change Notifier
Sends alert when IP changes
"""

import requests
import smtplib
from email.message import EmailMessage
from pathlib import Path

CACHE_FILE = Path.home() / ".last_ip"
EMAIL_FROM = "alerts@yourdomain.com"
EMAIL_TO = "you@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PASSWORD = "your_app_password"

def send_alert(old_ip, new_ip):
    msg = EmailMessage()
    msg.set_content(f"IP changed from {old_ip} to {new_ip}")
    msg["Subject"] = "🔔 IP Address Changed"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as smtp:
        smtp.login(EMAIL_FROM, SMTP_PASSWORD)
        smtp.send_message(msg)

def main():
    current_ip = requests.get("https://api.ipify.org").text
    old_ip = CACHE_FILE.read_text() if CACHE_FILE.exists() else None

    if old_ip != current_ip:
        print(f"IP changed: {old_ip} → {current_ip}")
        send_alert(old_ip or "unknown", current_ip)
        CACHE_FILE.write_text(current_ip)

if __name__ == "__main__":
    main()
```

### 2. Uptime Monitoring

**Free services that ping your API:**
- **UptimeRobot** (free, 50 monitors, 5-min checks)
- **Healthchecks.io** (free, cron monitoring)
- **Better Uptime** (free, 1-min checks)

**Self-hosted option:**

```bash
# Install Uptime Kuma (self-hosted)
docker run -d --restart=always \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  --name uptime-kuma \
  louislam/uptime-kuma:1
```

Access at: `http://localhost:3001`

### 3. ISP Considerations

**Will your ISP allow hosting?**

✅ **Most residential ISPs allow it** (check TOS)
⚠️ **Some block port 80/443** (use Cloudflare proxy to bypass)
⚠️ **Upload speed matters** (check your plan)

**Typical upload speeds:**
- Cable: 10-35 Mbps upload
- Fiber: 100-1000 Mbps upload (symmetrical)
- DSL: 1-10 Mbps upload (slow)

**For ML API**: 10 Mbps upload is fine for 10-50 concurrent users.

---

## Complete Deployment Script

```bash
#!/bin/bash
# Complete home hosting setup script

set -e

echo "🚀 Setting up home hosting for ML API..."

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y nginx certbot python3-certbot-nginx python3-pip docker.io docker-compose

# 3. Set up DDNS (Cloudflare example)
read -p "Enter Cloudflare API token: " CF_TOKEN
read -p "Enter Zone ID: " ZONE_ID
read -p "Enter domain (e.g., combos.yourdomain.com): " DOMAIN

cat > ~/cloudflare_ddns.py <<EOF
#!/usr/bin/env python3
# Cloudflare DDNS script (from earlier in this guide)
# ... (insert full script here) ...
EOF

chmod +x ~/cloudflare_ddns.py

# 4. Set up systemd timer
sudo cp cloudflare-ddns.service /etc/systemd/system/
sudo cp cloudflare-ddns.timer /etc/systemd/system/
sudo systemctl enable cloudflare-ddns.timer
sudo systemctl start cloudflare-ddns.timer

# 5. Configure Nginx
sudo tee /etc/nginx/sites-available/ml-api <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/ml-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. Get SSL certificate
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m you@example.com

# 7. Start ML API
cd /home/maxwell/vector-mtg/project-data-collection
docker-compose up -d

echo "✅ Setup complete!"
echo "Your API is available at: https://$DOMAIN"
```

---

## Troubleshooting

### DNS Not Updating

```bash
# Check if script is running
sudo systemctl status cloudflare-ddns.timer
sudo journalctl -u cloudflare-ddns.service -f

# Test DNS propagation
dig combos.yourdomain.com
nslookup combos.yourdomain.com 8.8.8.8

# Force update
sudo systemctl start cloudflare-ddns.service
```

### Can't Access from Internet

```bash
# Check if ports are open
sudo netstat -tulpn | grep -E ':(80|443)'

# Test from outside (use phone 4G, or online tool)
curl https://combos.yourdomain.com

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check Nginx config
sudo nginx -t
```

---

## Summary

**Best Setup for Home Hosting:**

1. ✅ **Cloudflare DDNS** (free, fast, custom domain)
2. ✅ **Systemd timer** (reliable updates every 5 min)
3. ✅ **Nginx reverse proxy** (handles SSL, routing)
4. ✅ **Let's Encrypt SSL** (free HTTPS)
5. ✅ **Docker Compose** (easy deployment)

**Total Cost**: $0-12/year (just domain registration)

**Your ML API will be:**
- ✅ Accessible via HTTPS
- ✅ Auto-updating DNS
- ✅ SSL-encrypted
- ✅ Production-ready

All on your home server with dynamic IP! 🎉
