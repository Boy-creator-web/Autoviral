#!/usr/bin/env bash
set -euo pipefail

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: jalankan sebagai root."
    exit 1
  fi
}

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

ensure_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: command '$1' tidak ditemukan."
    exit 1
  fi
}

ensure_firewall_cmd() {
  if command -v ufw >/dev/null 2>&1; then
    echo "ufw"
    return
  fi
  if command -v firewall-cmd >/dev/null 2>&1; then
    echo "firewalld"
    return
  fi
  echo "none"
}

ensure_docker_user_drop_rule() {
  local port="$1"
  if iptables -C DOCKER-USER -i eth0 -p tcp --dport "${port}" -j DROP >/dev/null 2>&1; then
    return 0
  fi
  iptables -I DOCKER-USER -i eth0 -p tcp --dport "${port}" -j DROP
}

persist_iptables_rules() {
  if ! command -v netfilter-persistent >/dev/null 2>&1; then
    log "Install iptables-persistent..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y iptables-persistent
  fi
  netfilter-persistent save >/dev/null
}

apply_ufw_rules() {
  ufw --force enable >/dev/null 2>&1 || true

  for allow_rule in OpenSSH 8000/tcp 4007/tcp; do
    if ! ufw status | grep -q "${allow_rule}"; then
      ufw allow "${allow_rule}"
    fi
  done

  for deny_rule in 5432/tcp 6379/tcp 5001/tcp 3000/tcp 7233/tcp 8080/tcp 8969/tcp; do
    if ! ufw status | grep -q "${deny_rule}"; then
      ufw deny "${deny_rule}"
    fi
  done
}

apply_firewalld_rules() {
  systemctl enable --now firewalld >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-service=ssh >/dev/null
  firewall-cmd --permanent --add-port=8000/tcp >/dev/null
  firewall-cmd --permanent --add-port=4007/tcp >/dev/null
  for p in 5432 6379 5001 3000 7233 8080 8969; do
    firewall-cmd --permanent --remove-port="${p}/tcp" >/dev/null 2>&1 || true
  done
  firewall-cmd --reload >/dev/null
}

container_env_get() {
  local key="$1"
  docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' autoviral-backend \
    | awk -F= -v k="${key}" '$1==k{print substr($0, index($0,"=")+1)}' | tail -n1 || true
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

recreate_backend_with_env_updates() {
  local updates_json="$1"
  local inspect_file env_file run_line
  inspect_file="$(mktemp)"
  env_file="$(mktemp)"
  run_line="$(mktemp)"

  docker inspect autoviral-backend > "${inspect_file}"

  python3 - "${inspect_file}" "${env_file}" "${run_line}" "${updates_json}" <<'PY'
import json
import shlex
import sys

inspect_path, env_path, run_path, updates_json = sys.argv[1:5]
updates = json.loads(updates_json)
obj = json.load(open(inspect_path))[0]

env_map = {}
for item in obj["Config"].get("Env", []):
    if "=" in item:
        k, v = item.split("=", 1)
        env_map[k] = v
for k, v in updates.items():
    env_map[k] = v

# Keep integration mapping valid JSON (older runs may have malformed string).
mapping_key = "POSTIZ_INTEGRATION_IDS_JSON"
default_mapping = '{"tiktok":"","instagram":"","youtube":"","facebook":"","x":"","linkedin":""}'
if mapping_key in env_map:
    try:
        parsed = json.loads(env_map[mapping_key])
        if not isinstance(parsed, dict):
            env_map[mapping_key] = default_mapping
    except Exception:
        env_map[mapping_key] = default_mapping

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

print("\n".join(networks[1:]))
PY

  local extra_nets
  extra_nets="$(python3 - "${inspect_file}" <<'PY'
import json, sys
obj = json.load(open(sys.argv[1]))[0]
nets = list((obj.get("NetworkSettings", {}).get("Networks") or {}).keys())
for n in nets[1:]:
    print(n)
PY
)"

  docker rm -f autoviral-backend >/dev/null
  sh -lc "$(cat "${run_line}")" >/dev/null
  if [ -n "${extra_nets}" ]; then
    echo "${extra_nets}" | while read -r net; do
      [ -n "${net}" ] && docker network connect "${net}" autoviral-backend >/dev/null 2>&1 || true
    done
  fi

  rm -f "${inspect_file}" "${env_file}" "${run_line}"
}

require_root
ensure_cmd docker
ensure_cmd python3
ensure_cmd iptables

firewall_mode="$(ensure_firewall_cmd)"
case "${firewall_mode}" in
  ufw)
    log "Firewall mode: UFW"
    apply_ufw_rules
    ;;
  firewalld)
    log "Firewall mode: firewalld"
    apply_firewalld_rules
    ;;
  none)
    log "WARN: UFW/firewalld tidak tersedia, lanjut dengan iptables DOCKER-USER saja."
    ;;
esac

# Docker publish sering bypass UFW/firewalld; blokir di DOCKER-USER chain.
for p in 5432 6379 5001 3000 7233 8080 8969; do
  ensure_docker_user_drop_rule "${p}"
done
persist_iptables_rules

secret="$(container_env_get SECRET_KEY)"
if [ -z "${secret}" ] || [ "${secret}" = "change-this-secret" ]; then
  secret="$(random_secret)"
  log "SECRET_KEY akan di-rotate."
else
  log "SECRET_KEY non-default terdeteksi, dipertahankan."
fi

api_key="$(container_env_get API_KEY)"
if [ -z "${api_key}" ]; then
  api_key="$(random_api_key)"
  log "API_KEY digenerate otomatis."
fi

updates="$(python3 - "${secret}" "${api_key}" <<'PY'
import json, sys
secret, api_key = sys.argv[1:3]
print(json.dumps({
    "SECRET_KEY": secret,
    "DOCS_ENABLED": "false",
    "API_KEY_REQUIRED": "true",
    "API_KEY": api_key,
    "POSTIZ_INTEGRATION_IDS_JSON": '{"tiktok":"","instagram":"","youtube":"","facebook":"","x":"","linkedin":""}',
}))
PY
)"

recreate_backend_with_env_updates "${updates}"

umask 077
{
  echo "AUTOVIRAL_API_KEY=${api_key}"
  echo "GENERATED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /root/autoviral-secrets.env

log "Hardening selesai."
log "API key backend tersimpan di /root/autoviral-secrets.env"
log "Gunakan header: X-API-Key: <AUTOVIRAL_API_KEY>"
