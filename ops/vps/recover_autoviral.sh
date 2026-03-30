#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/root/autoviral-backups}"
BACKUP_ID="${1:-latest}"

AUTOVIRAL_DB_CONTAINER="${AUTOVIRAL_DB_CONTAINER:-autoviral-postgres}"
AUTOVIRAL_DB_USER="${AUTOVIRAL_DB_USER:-autoviral}"
AUTOVIRAL_DB_NAME="${AUTOVIRAL_DB_NAME:-autoviral}"

POSTIZ_DB_CONTAINER="${POSTIZ_DB_CONTAINER:-postiz-postgres}"
POSTIZ_DB_USER="${POSTIZ_DB_USER:-postiz-user}"
POSTIZ_DB_NAME="${POSTIZ_DB_NAME:-postiz-db-local}"

POSTIZ_CONTAINER="${POSTIZ_CONTAINER:-postiz}"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -qx "$1"
}

resolve_backup_dir() {
  if [ "${BACKUP_ID}" = "latest" ]; then
    ls -1d "${BACKUP_ROOT}"/* 2>/dev/null | sort | tail -n 1
  else
    echo "${BACKUP_ROOT}/${BACKUP_ID}"
  fi
}

restore_postgres() {
  local container="$1"
  local user="$2"
  local db_name="$3"
  local dump_file="$4"

  if [ ! -f "${dump_file}" ]; then
    log "WARN: dump '${dump_file}' tidak ditemukan, skip restore ${db_name}"
    return 0
  fi

  if ! container_running "${container}"; then
    log "ERROR: container '${container}' tidak running. Jalankan container database dulu."
    return 1
  fi

  log "Restore database '${db_name}' ke container '${container}'..."
  gzip -dc "${dump_file}" | docker exec -i "${container}" psql -U "${user}" -d "${db_name}"
}

backup_dir="$(resolve_backup_dir)"
if [ -z "${backup_dir}" ] || [ ! -d "${backup_dir}" ]; then
  log "ERROR: backup tidak ditemukan. BACKUP_ROOT='${BACKUP_ROOT}', BACKUP_ID='${BACKUP_ID}'"
  exit 1
fi

log "Pakai backup: ${backup_dir}"

if docker ps --format '{{.Names}}' | grep -qx "${POSTIZ_CONTAINER}"; then
  log "Stop sementara '${POSTIZ_CONTAINER}' agar restore uploads konsisten..."
  docker stop "${POSTIZ_CONTAINER}" >/dev/null
fi

restore_postgres \
  "${AUTOVIRAL_DB_CONTAINER}" \
  "${AUTOVIRAL_DB_USER}" \
  "${AUTOVIRAL_DB_NAME}" \
  "${backup_dir}/db/autoviral.sql.gz"

restore_postgres \
  "${POSTIZ_DB_CONTAINER}" \
  "${POSTIZ_DB_USER}" \
  "${POSTIZ_DB_NAME}" \
  "${backup_dir}/db/postiz.sql.gz"

if [ -f "${backup_dir}/files/postiz-uploads.tar.gz" ]; then
  log "Restore uploads Postiz..."
  docker run --rm \
    -v postiz_uploads:/restore-target \
    -v "${backup_dir}/files:/backup-files:ro" \
    alpine:3.20 sh -lc '
      rm -rf /restore-target/*
      tar -xzf /backup-files/postiz-uploads.tar.gz -C /
      cp -a /uploads/. /restore-target/
    '
else
  log "WARN: backup uploads tidak ada, skip restore uploads"
fi

if [ -f "${backup_dir}/files/autoviral-code.tar.gz" ]; then
  log "Catatan: backup source code tersedia di '${backup_dir}/files/autoviral-code.tar.gz'"
fi

if ! docker ps --format '{{.Names}}' | grep -qx "${POSTIZ_CONTAINER}"; then
  log "Start kembali '${POSTIZ_CONTAINER}'..."
  docker start "${POSTIZ_CONTAINER}" >/dev/null
fi

log "Recovery selesai. Validasi manual:"
log "  - curl -sS http://127.0.0.1:8000/api/v1/health"
log "  - curl -sS http://127.0.0.1:5001/health"
log "  - curl -I http://127.0.0.1:4007"
