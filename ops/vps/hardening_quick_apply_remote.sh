#!/usr/bin/env bash
set -euo pipefail

# One-shot remote hardening helper for existing VPS setup.
# Safe to run multiple times (idempotent enough for current baseline).

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: jalankan sebagai root."
    exit 1
  fi
}

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

ensure_ufw_rule() {
  local action="$1"
  local rule="$2"
  if ! ufw status | grep -q "${rule}"; then
    ufw "${action}" "${rule}"
  fi
}

ensure_drop_rule() {
  local port="$1"
  if ! iptables -C DOCKER-USER -i eth0 -p tcp --dport "${port}" -j DROP >/dev/null 2>&1; then
    iptables -I DOCKER-USER -i eth0 -p tcp --dport "${port}" -j DROP
  fi
}

random_secret() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
}

random_api_key() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
}

require_root

if ! command -v ufw >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y ufw
fi

if ! command -v netfilter-persistent >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y iptables-persistent
fi

log "Apply UFW baseline..."
ufw --force enable >/dev/null 2>&1 || true
ensure_ufw_rule allow OpenSSH
ensure_ufw_rule allow 8000/tcp
ensure_ufw_rule allow 4007/tcp
ensure_ufw_rule deny 5432/tcp
ensure_ufw_rule deny 6379/tcp
ensure_ufw_rule deny 5001/tcp
ensure_ufw_rule deny 3000/tcp
ensure_ufw_rule deny 7233/tcp
ensure_ufw_rule deny 8080/tcp
ensure_ufw_rule deny 8969/tcp

log "Apply DOCKER-USER drops for published internal ports..."
for p in 5432 6379 5001 3000 7233 8080 8969; do
  ensure_drop_rule "${p}"
done
netfilter-persistent save >/dev/null

log "Read current autoviral-backend env..."
inspect_file="$(mktemp)"
env_file="$(mktemp)"
run_line="$(mktemp)"
docker inspect autoviral-backend > "${inspect_file}"

python3 - "${inspect_file}" "${env_file}" "${run_line}" <<'PY'
import json
import secrets
import shlex
import sys
from pathlib import Path

inspect_path, env_path, run_path = sys.argv[1:4]
obj = json.load(open(inspect_path))[0]

env_map = {}
for item in obj["Config"].get("Env", []):
    if "=" in item:
        k, v = item.split("=", 1)
        env_map[k] = v

if not env_map.get("SECRET_KEY") or env_map.get("SECRET_KEY") == "change-this-secret":
    env_map["SECRET_KEY"] = secrets.token_urlsafe(64)

env_map["DOCS_ENABLED"] = "false"
env_map["API_KEY_REQUIRED"] = "true"
if not env_map.get("API_KEY"):
    env_map["API_KEY"] = secrets.token_urlsafe(32)

Path("/root/autoviral-secrets.env").write_text(
    f"AUTOVIRAL_API_KEY={env_map['API_KEY']}\n"
    f"GENERATED_AT=auto\n",
    encoding="utf-8",
)

with open(env_path, "w", encoding="utf-8") as f:
    for k in sorted(env_map.keys()):
        f.write(f"{k}={env_map[k]}\n")

name = obj["Name"].lstrip("/")
image = obj["Config"]["Image"]
restart_name = obj["HostConfig"].get("RestartPolicy", {}).get("Name", "")
port_bindings = obj["HostConfig"].get("PortBindings", {}) or {}
networks = list((obj["NetworkSettings"].get("Networks") or {}).keys())
if not networks:
    raise SystemExit("Container autoviral-backend tidak punya network")

parts = ["docker run -d", f"--name {shlex.quote(name)}"]
if restart_name:
    parts.append(f"--restart {shlex.quote(restart_name)}")
parts.append(f"--env-file {shlex.quote(env_path)}")
parts.append(f"--network {shlex.quote(networks[0])}")

for container_port, bindings in port_bindings.items():
    if not bindings:
        continue
    for bind in bindings:
        host_port = bind.get("HostPort", "")
        host_ip = bind.get("HostIp", "")
        cport = container_port.split("/")[0]
        if host_ip and host_ip not in ("0.0.0.0", "::"):
            parts.append(f"-p {shlex.quote(host_ip + ':' + host_port + ':' + cport)}")
        else:
            parts.append(f"-p {shlex.quote(host_port + ':' + cport)}")

parts.append(shlex.quote(image))
with open(run_path, "w", encoding="utf-8") as f:
    f.write(" ".join(parts))
PY

docker rm -f autoviral-backend >/dev/null
sh -lc "$(cat "${run_line}")" >/dev/null
for net in postiz-app_postiz-network mirofish_default; do
  docker network connect "${net}" autoviral-backend >/dev/null 2>&1 || true
done

rm -f "${inspect_file}" "${env_file}" "${run_line}"

log "Hardening quick apply selesai."
log "Verifikasi cepat:"
log "  curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/docs   # expect 404"
log "  curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/v1/users/ # expect 401"
log "  cat /root/autoviral-secrets.env"
