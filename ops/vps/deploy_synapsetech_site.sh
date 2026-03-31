#!/usr/bin/env bash
set -euo pipefail

# Deploy static website for synapsetech.my.id with Nginx + Let's Encrypt.
# Assumptions:
# - repo path exists at /root/autoviral
# - Nginx and certbot are installed (script installs if missing)
# - backend API is proxied to 127.0.0.1:8000

DOMAIN="${DOMAIN:-synapsetech.my.id}"
WWW_DOMAIN="${WWW_DOMAIN:-www.synapsetech.my.id}"
SITE_ROOT="${SITE_ROOT:-/var/www/synapsetech-site}"
REPO_ROOT="${REPO_ROOT:-/root/autoviral}"
EMAIL="${LETSENCRYPT_EMAIL:-admin@synapsetech.my.id}"

echo "[1/6] Installing dependencies if needed..."
if ! command -v nginx >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y nginx
fi
if ! command -v certbot >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y certbot python3-certbot-nginx
fi

echo "[2/6] Preparing static site files..."
mkdir -p "${SITE_ROOT}"
cp -f "${REPO_ROOT}/website/index.html" "${SITE_ROOT}/index.html"
cp -f "${REPO_ROOT}/website/styles.css" "${SITE_ROOT}/styles.css"
cp -f "${REPO_ROOT}/website/script.js" "${SITE_ROOT}/script.js"

echo "[3/6] Writing Nginx site config..."
cat >/etc/nginx/sites-available/synapsetech-my-id.conf <<EOF
server {
    listen 80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    root ${SITE_ROOT};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 10m;
}
EOF

ln -sf /etc/nginx/sites-available/synapsetech-my-id.conf /etc/nginx/sites-enabled/synapsetech-my-id.conf
if [ -f /etc/nginx/sites-enabled/default ]; then
  rm -f /etc/nginx/sites-enabled/default
fi

echo "[4/6] Reloading Nginx..."
nginx -t
systemctl restart nginx

echo "[5/6] Requesting SSL certificate..."
certbot --nginx \
  -d "${DOMAIN}" \
  -d "${WWW_DOMAIN}" \
  --non-interactive \
  --agree-tos \
  --email "${EMAIL}" \
  --redirect

echo "[6/6] Final health checks..."
curl -fsS "https://${DOMAIN}" >/dev/null
curl -fsS "https://${DOMAIN}/api/v1/health" >/dev/null

echo "Deployment complete: https://${DOMAIN}"
