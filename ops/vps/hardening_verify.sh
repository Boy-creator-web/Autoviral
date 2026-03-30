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

check_not_listening_public() {
  local port="$1"
  if ss -tuln | awk '{print $5}' | grep -Eq "0\\.0\\.0\\.0:${port}$|\\[::\\]:${port}$"; then
    ko "Port ${port} masih listen publik"
  else
    ok "Port ${port} tidak listen publik"
  fi
}

check_not_listening_public 5432
check_not_listening_public 6379
check_not_listening_public 5001
check_not_listening_public 3000
check_not_listening_public 7233
check_not_listening_public 8080
check_not_listening_public 8969

if ufw status | grep -q "Status: active"; then
  ok "UFW aktif"
else
  ko "UFW tidak aktif"
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
if [ "${docs_code}" = "404" ]; then
  ok "Swagger docs disabled -> ${docs_code}"
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
