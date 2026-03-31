#!/usr/bin/env bash
set -euo pipefail

# Restore PostgreSQL backup into docker-compose service.
# Usage:
#   ./backup/restore_postgres.sh /root/autoviral/backups/autoviral_YYYYmmdd_HHMMSS.sql.gz

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /path/to/autoviral_backup.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"
DB_CONTAINER="${DB_CONTAINER:-autoviral-postgres}"
DB_NAME="${DB_NAME:-autoviral}"
DB_USER="${DB_USER:-autoviral}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "[ERROR] Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
  echo "[ERROR] Container ${DB_CONTAINER} is not running"
  exit 1
fi

echo "[WARN] This will overwrite data in ${DB_NAME}."
read -r -p "Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "[INFO] Restore cancelled"
  exit 0
fi

echo "[INFO] Dropping and recreating public schema"
docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "[INFO] Restoring from ${BACKUP_FILE}"
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"

echo "[OK] Restore completed"
