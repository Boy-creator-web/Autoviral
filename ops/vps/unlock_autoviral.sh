#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/root/autoviral}"
SITE_ROOT="${SITE_ROOT:-/var/www/synapsetech-site}"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

unlock_file_if_exists() {
  local path="$1"
  if [ -f "${path}" ]; then
    chattr -i "${path}" || true
  fi
}

log "Unlock immutable flag pada file kritikal..."
unlock_file_if_exists "${REPO_ROOT}/backend/.env"
unlock_file_if_exists "${SITE_ROOT}/checkout.html"
unlock_file_if_exists "${SITE_ROOT}/checkout.js"
unlock_file_if_exists "${SITE_ROOT}/styles.css"
unlock_file_if_exists "/etc/nginx/sites-available/synapsetech-my-id.conf"

log "Selesai unlock. Anda bisa melakukan update/deploy kembali."
