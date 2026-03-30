#!/usr/bin/env bash
set -euo pipefail

fail=0

ok() {
  echo "[OK] $*"
}

ko() {
  echo "[FAIL] $*"
  fail=1
}

if systemctl is-active --quiet nginx; then
  ok "nginx aktif"
else
  ko "nginx tidak aktif"
fi

if systemctl is-active --quiet fail2ban; then
  ok "fail2ban aktif"
else
  ko "fail2ban tidak aktif"
fi

health_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/health || true)"
if [ "${health_code}" = "200" ]; then
  ok "Nginx health proxy /health -> 200"
else
  ko "Nginx health proxy /health -> ${health_code}"
fi

users_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/api/v1/users/ || true)"
if [ "${users_code}" = "401" ]; then
  ok "API tetap terproteksi via Nginx (users -> 401 tanpa key)"
else
  ko "Expected 401 tanpa key via Nginx, got ${users_code}"
fi

if [ -f /root/autoviral-secrets.env ]; then
  api_key="$(awk -F= '/^AUTOVIRAL_API_KEY=/{print $2}' /root/autoviral-secrets.env | tail -n1)"
  auth_code="$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-Key: ${api_key}" http://127.0.0.1/api/v1/users/ || true)"
  if [ "${auth_code}" = "200" ]; then
    ok "API via Nginx accessible with X-API-Key"
  else
    ko "API via Nginx expected 200 with X-API-Key, got ${auth_code}"
  fi
else
  ko "/root/autoviral-secrets.env tidak ditemukan"
fi

if fail2ban-client status nginx-autoviral >/dev/null 2>&1; then
  ok "Fail2ban jail nginx-autoviral terdaftar"
else
  ko "Fail2ban jail nginx-autoviral tidak terdaftar"
fi

if [ "${fail}" -ne 0 ]; then
  echo "Hardening phase 2 verify selesai dengan masalah."
  exit 1
fi

echo "Hardening phase 2 verify selesai: semua OK."
