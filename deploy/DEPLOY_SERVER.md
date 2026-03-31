# Autoviral Deployment Guide (synapsetech.my.id)

Panduan ini memasang website + API Autoviral di server Ubuntu.

## 1) Pull kode terbaru

```bash
cd /root/autoviral
git pull origin cursor/mesin-scraper-autoviral-a805
```

## 2) Jalankan backend (Docker Compose)

```bash
cd /root/autoviral
docker compose down
docker compose up -d --build
```

Cek health backend lokal:

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

## 3) Pasang landing page

```bash
sudo mkdir -p /var/www/autoviral
sudo cp /root/autoviral/frontend/index.html /var/www/autoviral/index.html
sudo chown -R www-data:www-data /var/www/autoviral
```

## 4) Pasang Nginx final config

```bash
sudo cp /root/autoviral/deploy/nginx/synapsetech-my-id.conf /etc/nginx/sites-available/synapsetech-my-id.conf
sudo ln -sf /etc/nginx/sites-available/synapsetech-my-id.conf /etc/nginx/sites-enabled/synapsetech-my-id.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 5) Pastikan SSL aktif (jika belum)

```bash
sudo certbot --nginx -d synapsetech.my.id -d www.synapsetech.my.id --redirect --agree-tos -m admin@synapsetech.my.id --non-interactive
sudo nginx -t && sudo systemctl reload nginx
```

## 6) Verifikasi publik

```bash
curl -I http://synapsetech.my.id
curl -I https://synapsetech.my.id
curl -s https://synapsetech.my.id/api/v1/health
curl -I https://synapsetech.my.id/docs
```

Hasil normal:
- HTTP -> 301 ke HTTPS
- HTTPS -> 200
- `/api/v1/health` -> JSON `{ "message": "ok" }`
- `/docs` -> 200
