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

check_port_protection() {
  local port="$1"
  local listening
  listening="$(ss -tuln | awk '{print $5}' | grep -E "0\\.0\\.0\\.0:${port}$|\\[::\\]:${port}$" || true)"
  if [ -z "${listening}" ]; then
    ok "Port ${port} tidak listen publik"
    return
  fi

  if iptables -C DOCKER-USER -i eth0 -p tcp --dport "${port}" -j DROP >/dev/null 2>&1; then
    ok "Port ${port} listen publik tapi diblokir DOCKER-USER"
  else
    ko "Port ${port} listen publik dan tidak diblokir"
  fi
}

check_port_protection 5432
check_port_protection 6379
check_port_protection 5001
check_port_protection 3000
check_port_protection 7233
check_port_protection 8080
check_port_protection 8969

if command -v ufw >/dev/null 2>&1; then
  if ufw status | grep -q "Status: active"; then
    ok "UFW aktif"
  else
    ko "UFW tidak aktif"
  fi
else
  ok "UFW tidak terpasang (expected on current host), rely on DOCKER-USER iptables"
fi

for endpoint in \
  "http://127.0.0.1:8000/api/v1/health" \
  "http://127.0.0.1:5001/health" \
  "http://127.0.0.1:4007/auth"
do
  code="$(curl -s -o /dev/null -w '%{http_code}' "${endpoint}" || true)"
  if [ "${code}" = "200" ] || [ "${code}" = "301" ] || [ "${code}" = "302" ] || [ "${code}" = "307" ]; then
    ok "${endpoint} -> ${code}"
  else
    ko "${endpoint} -> ${code}"
  fi
done

docs_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/docs || true)"
if [ "${docs_code}" = "404" ] || [ "${docs_code}" = "401" ]; then
  ok "Swagger docs protected/disabled -> ${docs_code}"
else
  ko "Swagger docs expected 404, got ${docs_code}"
fi

unauth_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/v1/users/ || true)"
if [ "${unauth_code}" = "401" ]; then
  ok "Users endpoint protected (without API key) -> ${unauth_code}"
else
  ko "Users endpoint should be 401 without API key, got ${unauth_code}"
fi

if [ -f /root/autoviral-secrets.env ]; then
  api_key="$(awk -F= '/^AUTOVIRAL_API_KEY=/{print $2}' /root/autoviral-secrets.env | tail -n1)"
  if [ -n "${api_key}" ]; then
    auth_code="$(curl -s -o /dev/null -w '%{http_code}' -H "X-API-Key: ${api_key}" http://127.0.0.1:8000/api/v1/users/ || true)"
    if [ "${auth_code}" = "200" ]; then
      ok "Users endpoint accessible with X-API-Key -> ${auth_code}"
    else
      ko "Users endpoint expected 200 with X-API-Key, got ${auth_code}"
    fi
  else
    ko "/root/autoviral-secrets.env ada tapi AUTOVIRAL_API_KEY kosong"
  fi
else
  ko "/root/autoviral-secrets.env tidak ditemukan"
fi

if [ "${fail}" -ne 0 ]; then
  echo "Hardening verify selesai dengan masalah."
  exit 1
fi

echo "Hardening verify selesai: semua OK."
