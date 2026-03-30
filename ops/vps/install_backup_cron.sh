#!/usr/bin/env bash
set -euo pipefail

BACKUP_SCRIPT_PATH="${BACKUP_SCRIPT_PATH:-/root/autoviral/ops/vps/backup_autoviral.sh}"
CRON_SCHEDULE="${CRON_SCHEDULE:-30 2 * * *}"
LOG_FILE="${LOG_FILE:-/var/log/autoviral-backup.log}"

if [ ! -f "${BACKUP_SCRIPT_PATH}" ]; then
  echo "ERROR: backup script tidak ditemukan di '${BACKUP_SCRIPT_PATH}'"
  echo "Copy file dari repo dulu, lalu jalankan lagi."
  exit 1
fi

chmod +x "${BACKUP_SCRIPT_PATH}"

CRON_LINE="${CRON_SCHEDULE} ${BACKUP_SCRIPT_PATH} >> ${LOG_FILE} 2>&1"

tmp_cron="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${BACKUP_SCRIPT_PATH}" > "${tmp_cron}" || true
echo "${CRON_LINE}" >> "${tmp_cron}"
crontab "${tmp_cron}"
rm -f "${tmp_cron}"

echo "Cron backup terpasang:"
echo "  ${CRON_LINE}"
