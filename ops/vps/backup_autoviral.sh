#!/usr/bin/env bash
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/root/autoviral-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
AUTOVIRAL_CODE_DIR="${AUTOVIRAL_CODE_DIR:-/root/autoviral}"

AUTOVIRAL_DB_CONTAINER="${AUTOVIRAL_DB_CONTAINER:-autoviral-postgres}"
AUTOVIRAL_DB_USER="${AUTOVIRAL_DB_USER:-autoviral}"
AUTOVIRAL_DB_NAME="${AUTOVIRAL_DB_NAME:-autoviral}"

POSTIZ_DB_CONTAINER="${POSTIZ_DB_CONTAINER:-postiz-postgres}"
POSTIZ_DB_USER="${POSTIZ_DB_USER:-postiz-user}"
POSTIZ_DB_NAME="${POSTIZ_DB_NAME:-postiz-db-local}"

POSTIZ_CONTAINER="${POSTIZ_CONTAINER:-postiz}"
MIROFISH_CONTAINER="${MIROFISH_CONTAINER:-mirofish}"
AUTOVIRAL_BACKEND_CONTAINER="${AUTOVIRAL_BACKEND_CONTAINER:-autoviral-backend}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="${BACKUP_ROOT}/${timestamp}"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

container_exists() {
  docker ps -a --format '{{.Names}}' | grep -qx "$1"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -qx "$1"
}

backup_postgres() {
  local container="$1"
  local user="$2"
  local db_name="$3"
  local out_file="$4"

  if ! container_running "${container}"; then
    log "WARN: container '${container}' tidak running, skip dump ${db_name}"
    return 0
  fi

  log "Dump PostgreSQL '${db_name}' dari '${container}'..."
  docker exec "${container}" pg_dump -U "${user}" -d "${db_name}" | gzip -9 > "${out_file}"
  if [ ! -s "${out_file}" ]; then
    log "ERROR: dump '${out_file}' kosong"
    return 1
  fi
}

mkdir -p "${backup_dir}/db" "${backup_dir}/files" "${backup_dir}/meta"
chmod 700 "${backup_dir}"

log "Backup root: ${backup_dir}"

backup_postgres \
  "${AUTOVIRAL_DB_CONTAINER}" \
  "${AUTOVIRAL_DB_USER}" \
  "${AUTOVIRAL_DB_NAME}" \
  "${backup_dir}/db/autoviral.sql.gz"

backup_postgres \
  "${POSTIZ_DB_CONTAINER}" \
  "${POSTIZ_DB_USER}" \
  "${POSTIZ_DB_NAME}" \
  "${backup_dir}/db/postiz.sql.gz"

if [ -d "${AUTOVIRAL_CODE_DIR}" ]; then
  log "Backup source code '${AUTOVIRAL_CODE_DIR}'..."
  tar -czf "${backup_dir}/files/autoviral-code.tar.gz" \
    -C "$(dirname "${AUTOVIRAL_CODE_DIR}")" \
    "$(basename "${AUTOVIRAL_CODE_DIR}")"
else
  log "WARN: '${AUTOVIRAL_CODE_DIR}' tidak ditemukan, skip backup source code"
fi

if container_running "${POSTIZ_CONTAINER}"; then
  log "Backup uploads Postiz..."
  docker exec "${POSTIZ_CONTAINER}" sh -lc 'tar -czf - -C / uploads 2>/dev/null || true' \
    > "${backup_dir}/files/postiz-uploads.tar.gz"
else
  log "WARN: '${POSTIZ_CONTAINER}' tidak running, skip backup uploads"
fi

log "Simpan metadata stack..."
docker ps -a > "${backup_dir}/meta/docker-ps-a.txt"
docker images > "${backup_dir}/meta/docker-images.txt"
docker volume ls > "${backup_dir}/meta/docker-volumes.txt"
docker network ls > "${backup_dir}/meta/docker-networks.txt"

if [ -d "${AUTOVIRAL_CODE_DIR}/.git" ]; then
  git -C "${AUTOVIRAL_CODE_DIR}" rev-parse HEAD > "${backup_dir}/meta/autoviral-git-head.txt" || true
  git -C "${AUTOVIRAL_CODE_DIR}" status --short --branch > "${backup_dir}/meta/autoviral-git-status.txt" || true
fi

if container_exists "${AUTOVIRAL_BACKEND_CONTAINER}"; then
  docker inspect "${AUTOVIRAL_BACKEND_CONTAINER}" > "${backup_dir}/meta/autoviral-backend.inspect.json"
  docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${AUTOVIRAL_BACKEND_CONTAINER}" \
    > "${backup_dir}/meta/autoviral-backend.env"
fi

if container_exists "${POSTIZ_CONTAINER}"; then
  docker inspect "${POSTIZ_CONTAINER}" > "${backup_dir}/meta/postiz.inspect.json"
fi

if container_exists "${MIROFISH_CONTAINER}"; then
  docker inspect "${MIROFISH_CONTAINER}" > "${backup_dir}/meta/mirofish.inspect.json"
fi

log "Apply retention: hapus backup lebih tua dari ${RETENTION_DAYS} hari..."
find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d -mtime +"${RETENTION_DAYS}" -print -exec rm -rf {} +

log "Backup selesai: ${backup_dir}"
