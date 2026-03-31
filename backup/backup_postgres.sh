#!/usr/bin/env bash
set -euo pipefail

# Create PostgreSQL backup from docker-compose service.
# Usage:
#   ./backup/backup_postgres.sh
# Optional env vars:
#   BACKUP_DIR, DB_CONTAINER, DB_NAME, DB_USER

BACKUP_DIR="${BACKUP_DIR:-/root/autoviral/backups}"
DB_CONTAINER="${DB_CONTAINER:-autoviral-postgres}"
DB_NAME="${DB_NAME:-autoviral}"
DB_USER="${DB_USER:-autoviral}"

mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="$BACKUP_DIR/autoviral_${TS}.sql.gz"

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
  echo "[ERROR] Container ${DB_CONTAINER} is not running"
  exit 1
fi

echo "[INFO] Creating backup to ${OUT_FILE}"
docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT_FILE"
echo "[OK] Backup created: ${OUT_FILE}"

# Keep last 14 backups by default
KEEP_COUNT="${KEEP_COUNT:-14}"
ls -1t "$BACKUP_DIR"/autoviral_*.sql.gz 2>/dev/null | tail -n +$((KEEP_COUNT + 1)) | xargs -r rm -f
