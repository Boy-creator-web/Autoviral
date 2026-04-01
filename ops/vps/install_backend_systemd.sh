#!/usr/bin/env bash
set -euo pipefail

# Install a persistent systemd service for Autoviral backend container.
# This removes manual docker run steps and ensures auto-start on reboot.

AUTOVIRAL_CODE_DIR="${AUTOVIRAL_CODE_DIR:-/root/autoviral}"
BACKEND_IMAGE="${BACKEND_IMAGE:-autoviral-backend-fix}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-autoviral-backend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
DATABASE_URL_OVERRIDE="${DATABASE_URL_OVERRIDE:-postgresql+psycopg2://autoviral:autoviral@127.0.0.1:5432/autoviral}"

RUNNER_PATH="/usr/local/bin/run-autoviral-backend.sh"
UNIT_PATH="/etc/systemd/system/autoviral-backend.service"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

if ! command -v docker >/dev/null 2>&1; then
  log "ERROR: docker not found"
  exit 1
fi

if [ ! -d "${AUTOVIRAL_CODE_DIR}/backend" ]; then
  log "ERROR: backend directory not found at ${AUTOVIRAL_CODE_DIR}/backend"
  exit 1
fi

if [ ! -f "${AUTOVIRAL_CODE_DIR}/backend/.env" ]; then
  log "ERROR: missing ${AUTOVIRAL_CODE_DIR}/backend/.env"
  exit 1
fi

log "Build backend image '${BACKEND_IMAGE}'..."
docker build -t "${BACKEND_IMAGE}" "${AUTOVIRAL_CODE_DIR}/backend"

log "Write backend runner '${RUNNER_PATH}'..."
cat > "${RUNNER_PATH}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
docker rm -f ${BACKEND_CONTAINER} >/dev/null 2>&1 || true
exec docker run \\
  --name ${BACKEND_CONTAINER} \\
  --network host \\
  --env-file ${AUTOVIRAL_CODE_DIR}/backend/.env \\
  -e DATABASE_URL=${DATABASE_URL_OVERRIDE} \\
  -p ${BACKEND_PORT}:8000 \\
  ${BACKEND_IMAGE}
EOF
chmod 755 "${RUNNER_PATH}"

log "Write systemd unit '${UNIT_PATH}'..."
cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=Autoviral Backend Container Service
After=network-online.target docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=5
ExecStart=${RUNNER_PATH}
ExecStop=/usr/bin/docker stop -t 15 ${BACKEND_CONTAINER}
ExecStopPost=/usr/bin/docker rm -f ${BACKEND_CONTAINER}

[Install]
WantedBy=multi-user.target
EOF

log "Enable and restart service..."
systemctl daemon-reload
systemctl enable autoviral-backend.service
systemctl restart autoviral-backend.service

log "Service status:"
systemctl --no-pager --full status autoviral-backend.service | sed -n '1,25p'

log "Backend health check..."
curl -fsS "http://127.0.0.1:8000/api/v1/health"
echo
log "Done. Backend is now managed by systemd."
