#!/usr/bin/env bash
set -u

AUTOVIRAL_DIR="${AUTOVIRAL_DIR:-/root/autoviral}"
LOCK_PATHS=(
  "${AUTOVIRAL_DIR}/backend/.env"
  "${AUTOVIRAL_DIR}/website/checkout.html"
  "${AUTOVIRAL_DIR}/website/checkout.js"
  "${AUTOVIRAL_DIR}/website/styles.css"
  "/etc/nginx/sites-available/synapsetech-my-id.conf"
)

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

if [ "$(id -u)" -ne 0 ]; then
  echo "Jalankan script ini sebagai root."
  exit 1
fi

if [ ! -d "${AUTOVIRAL_DIR}" ]; then
  echo "Directory '${AUTOVIRAL_DIR}' tidak ditemukan."
  exit 1
fi

cd "${AUTOVIRAL_DIR}" || exit 1

log "Install dependencies file attr tools bila perlu..."
apt-get update -y >/dev/null 2>&1 || true
apt-get install -y e2fsprogs >/dev/null 2>&1 || true

log "Run backup terbaru sebelum lock..."
chmod +x "${AUTOVIRAL_DIR}/ops/vps/backup_autoviral.sh"
"${AUTOVIRAL_DIR}/ops/vps/backup_autoviral.sh"

log "Verifikasi endpoint health + checkout..."
health_code="$(curl -s -o /dev/null -w '%{http_code}' https://synapsetech.my.id/api/v1/health)"
checkout_code="$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST https://synapsetech.my.id/api/v1/customer-intake/checkout \
  -H "Content-Type: application/json" \
  -d '{}')"
echo "health_code=${health_code}"
echo "checkout_code=${checkout_code}"

if [ "${health_code}" != "200" ]; then
  log "WARN: health endpoint bukan 200."
fi
if [ "${checkout_code}" != "422" ]; then
  log "WARN: checkout endpoint bukan 422 untuk payload kosong."
fi

log "Lock file kritikal agar tidak berubah tanpa unlock..."
for file_path in "${LOCK_PATHS[@]}"; do
  if [ -e "${file_path}" ]; then
    chattr +i "${file_path}" 2>/dev/null \
      && log "LOCKED: ${file_path}" \
      || log "WARN: gagal lock '${file_path}' (filesystem mungkin tidak support chattr)."
  else
    log "SKIP lock (not found): ${file_path}"
  fi
done

cat <<'EOF'

Selesai.
Cara unlock saat perlu update:
  chattr -i /root/autoviral/backend/.env
  chattr -i /root/autoviral/website/checkout.html
  chattr -i /root/autoviral/website/checkout.js
  chattr -i /root/autoviral/website/styles.css
  chattr -i /etc/nginx/sites-available/synapsetech-my-id.conf

EOF
