#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="${1:-$repository_root/fixtures/fastapi-postgres}"
fixture_name="$(basename "$fixture")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for local fixture validation." >&2
  exit 2
fi

if [[ "$fixture_name" == *redis* ]]; then
  export APP_PORT="${APP_PORT:-18001}"
  export POSTGRES_PORT="${POSTGRES_PORT:-15433}"
  export REDIS_PORT="${REDIS_PORT:-16379}"
  export REDIS_PASSWORD="fixture-local-only-cache-password"
else
  export APP_PORT="${APP_PORT:-18000}"
  export POSTGRES_PORT="${POSTGRES_PORT:-15432}"
fi

compose=(docker compose -f "$fixture/compose.yaml" -f "$fixture/compose.dev.yaml")
health_file="$(mktemp -t deploy-skills-local-health.XXXXXX)"
completed=0

cleanup() {
  if [[ "$completed" -ne 1 ]]; then
    "${compose[@]}" logs --no-color --tail=200 || true
  fi
  "${compose[@]}" down --remove-orphans || true
  rm -f "$health_file"
}
trap cleanup EXIT

python3 "$repository_root/skills/configure-local-compose/scripts/validate_local_compose.py" --root "$fixture"
"${compose[@]}" build app
services="$("${compose[@]}" --profile '*' config --services)"
dependencies=(db)
if grep -qx redis <<<"$services"; then
  dependencies+=(redis)
fi
"${compose[@]}" up -d "${dependencies[@]}"
"${compose[@]}" --profile tools run --rm migrate
"${compose[@]}" up -d app

healthy=0
for _attempt in $(seq 1 45); do
  if curl --fail --silent "http://127.0.0.1:$APP_PORT/health" > "$health_file"; then
    healthy=1
    break
  fi
  sleep 2
done
if [[ "$healthy" -ne 1 ]]; then
  echo "Local fixture did not become healthy." >&2
  exit 1
fi

grep -q '"database":"reachable"' "$health_file"
if grep -qx redis <<<"$services"; then
  grep -q '"redis":"reachable"' "$health_file"
fi

app_container_id="$("${compose[@]}" ps -q app)"
runtime_uid="$("${compose[@]}" exec -T app id -u)"
if [[ "$runtime_uid" == "0" ]]; then
  echo "Local application container runs as root." >&2
  exit 1
fi
docker inspect --format '{{json .Config.Cmd}}' "$app_container_id" \
  | python3 -c 'import json, sys; command = " ".join(json.load(sys.stdin) or []); raise SystemExit("--reload" not in command)'
docker inspect --format '{{json .Mounts}}' "$app_container_id" \
  | python3 -c 'import json, sys; mounts = json.load(sys.stdin); raise SystemExit(not any(item.get("Type") == "bind" and item.get("Destination") == "/app/app" for item in mounts))'
for dependency in "${dependencies[@]}"; do
  dependency_container_id="$("${compose[@]}" ps -q "$dependency")"
  docker inspect --format '{{json .NetworkSettings.Ports}}' "$dependency_container_id" \
    | python3 -c 'import json, sys; ports = json.load(sys.stdin); bindings = [binding for values in ports.values() for binding in (values or [])]; raise SystemExit(not bindings or any(binding.get("HostIp") != "127.0.0.1" for binding in bindings))'
done

completed=1
echo "Local fixture passed: reload command, source bind mount, migration, dependency health, and non-root runtime."
