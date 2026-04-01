#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

fail=0

check_http() {
  local name="$1"
  local url="$2"
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' "${url}" || true)"
  if [ "${code}" = "200" ]; then
    log "OK: ${name} (${url}) -> ${code}"
  else
    log "FAIL: ${name} (${url}) -> ${code}"
    fail=1
  fi
}

check_container() {
  local name="$1"
  if docker ps --format '{{.Names}}' | grep -qx "${name}"; then
    log "OK: container '${name}' running"
  else
    log "FAIL: container '${name}' not running"
    fail=1
  fi
}

check_container autoviral-backend
check_container autoviral-postgres
check_container autoviral-redis
check_container postiz
check_container postiz-postgres
check_container postiz-redis
check_container mirofish

check_http "Autoviral Health" "http://127.0.0.1:8000/api/v1/health"
check_http "MiroFish Health" "http://127.0.0.1:5001/health"

if docker ps --format '{{.Names}}' | grep -qx "autoviral-celery-worker"; then
  log "OK: container 'autoviral-celery-worker' running"
else
  log "WARN: container 'autoviral-celery-worker' not running (Celery async tasks disabled)"
fi

# Postiz root biasanya redirect ke /auth (307); status ini dianggap sehat.
postiz_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4007 || true)"
if [ "${postiz_code}" = "200" ] || [ "${postiz_code}" = "301" ] || [ "${postiz_code}" = "302" ] || [ "${postiz_code}" = "307" ]; then
  log "OK: Postiz root reachable -> ${postiz_code}"
else
  log "FAIL: Postiz root not reachable -> ${postiz_code}"
  fail=1
fi

if [ "${fail}" -ne 0 ]; then
  log "Healthcheck selesai dengan error."
  exit 1
fi

log "Healthcheck stack selesai: semua OK."
