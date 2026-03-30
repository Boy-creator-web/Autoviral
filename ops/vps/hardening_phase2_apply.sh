#!/usr/bin/env bash
set -euo pipefail

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: jalankan sebagai root."
    exit 1
  fi
}

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

ensure_pkg() {
  local pkg="$1"
  if ! dpkg -s "${pkg}" >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y "${pkg}"
  fi
}

require_root

log "Install package hardening fase 2..."
export DEBIAN_FRONTEND=noninteractive
ensure_pkg nginx
ensure_pkg fail2ban

log "Generate Nginx reverse-proxy config for Autoviral..."
cat >/etc/nginx/sites-available/autoviral.conf <<'NGINX'
limit_req_zone $binary_remote_addr zone=autoviral_api_limit:10m rate=20r/m;
limit_conn_zone $binary_remote_addr zone=autoviral_conn_limit:10m;

map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    access_log /var/log/nginx/autoviral-access.log;
    error_log /var/log/nginx/autoviral-error.log warn;

    location = /health {
        proxy_pass http://127.0.0.1:8000/api/v1/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        limit_req zone=autoviral_api_limit burst=40 nodelay;
        limit_conn autoviral_conn_limit 30;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_read_timeout 90s;
        proxy_connect_timeout 15s;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

if [ -f /etc/nginx/sites-enabled/default ]; then
  rm -f /etc/nginx/sites-enabled/default
fi
ln -sf /etc/nginx/sites-available/autoviral.conf /etc/nginx/sites-enabled/autoviral.conf

log "Validate and reload Nginx..."
nginx -t
systemctl enable nginx >/dev/null
systemctl restart nginx

log "Create fail2ban jail for nginx auth/rate abuse..."
mkdir -p /etc/fail2ban/jail.d /etc/fail2ban/filter.d

cat >/etc/fail2ban/filter.d/nginx-autoviral.conf <<'F2BFILTER'
[Definition]
failregex = ^<HOST> -.*"(GET|POST|PUT|PATCH|DELETE|HEAD).*" 401
            ^<HOST> -.*"(GET|POST|PUT|PATCH|DELETE|HEAD).*" 429
ignoreregex =
F2BFILTER

cat >/etc/fail2ban/jail.d/autoviral.conf <<'F2BJAIL'
[nginx-http-auth]
enabled = true

[nginx-botsearch]
enabled = true

[nginx-autoviral]
enabled = true
port = http,https
filter = nginx-autoviral
logpath = /var/log/nginx/autoviral-access.log
maxretry = 20
findtime = 10m
bantime = 1h
backend = auto
F2BJAIL

systemctl enable fail2ban >/dev/null
systemctl restart fail2ban

log "If UFW exists, allow 80/tcp."
if command -v ufw >/dev/null 2>&1; then
  if ! ufw status | grep -q "80/tcp"; then
    ufw allow 80/tcp
  fi
fi

log "Hardening phase 2 selesai."
log "Endpoint utama via Nginx: http://$(hostname -I | awk '{print $1}')/health"
