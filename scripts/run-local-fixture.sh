#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="${1:-$repository_root/fixtures/fastapi-postgres}"
fixture_name="$(basename "$fixture")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for local fixture validation." >&2
  exit 2
fi

case "$fixture_name" in
  *nextjs*)
    export APP_PORT="${APP_PORT:-13000}"
    health_path="/api/health"
    ;;
  *node-api*)
    export APP_PORT="${APP_PORT:-18003}"
    export POSTGRES_PORT="${POSTGRES_PORT:-15434}"
    health_path="/health"
    ;;
  *spring-boot*)
    export APP_PORT="${APP_PORT:-18004}"
    export POSTGRES_PORT="${POSTGRES_PORT:-15435}"
    health_path="/health"
    ;;
  *redis*)
    export APP_PORT="${APP_PORT:-18001}"
    export POSTGRES_PORT="${POSTGRES_PORT:-15433}"
    export REDIS_PORT="${REDIS_PORT:-16379}"
    export REDIS_PASSWORD="fixture-local-only-cache-password"
    health_path="/health"
    ;;
  *)
    export APP_PORT="${APP_PORT:-18000}"
    export POSTGRES_PORT="${POSTGRES_PORT:-15432}"
    health_path="/health"
    ;;
esac

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
dependencies=()
if grep -qx db <<<"$services"; then
  dependencies+=(db)
fi
if grep -qx redis <<<"$services"; then
  dependencies+=(redis)
fi
if [[ "${#dependencies[@]}" -gt 0 ]]; then
  "${compose[@]}" up -d "${dependencies[@]}"
fi
if grep -qx migrate <<<"$services"; then
  "${compose[@]}" --profile tools run --rm migrate
fi
"${compose[@]}" up -d app

healthy=0
for _attempt in $(seq 1 45); do
  if curl --fail --silent "http://127.0.0.1:$APP_PORT$health_path" > "$health_file"; then
    healthy=1
    break
  fi
  sleep 2
done
if [[ "$healthy" -ne 1 ]]; then
  echo "Local fixture did not become healthy." >&2
  exit 1
fi

if grep -qx db <<<"$services"; then
  grep -q '"database":"reachable"' "$health_file"
fi
if grep -qx redis <<<"$services"; then
  grep -q '"redis":"reachable"' "$health_file"
fi

app_container_id="$("${compose[@]}" ps -q app)"
configured_user="$(docker inspect --format '{{.Config.User}}' "$app_container_id")"
if [[ -z "$configured_user" || "$configured_user" == "0" || "$configured_user" == "root" || "$configured_user" == 0:* ]]; then
  echo "Local application container has no explicit non-root runtime user." >&2
  exit 1
fi
if runtime_uid="$("${compose[@]}" exec -T app id -u 2>/dev/null)" && [[ "$runtime_uid" == "0" ]]; then
  echo "Local application container resolves its configured user to root." >&2
  exit 1
fi
docker inspect --format '{{json .Config.Cmd}}' "$app_container_id" \
  | python3 -c 'import json, sys; command = " ".join(json.load(sys.stdin) or []).lower(); markers = ("reload", "--watch", "next dev", "npm run dev", "pnpm run dev", "yarn dev", "bun run dev", "vite", "spring-boot:run"); raise SystemExit(not any(marker in command for marker in markers))'
docker inspect --format '{{json .Mounts}}' "$app_container_id" \
  | python3 -c 'import json, sys; mounts = json.load(sys.stdin); raise SystemExit(not any(item.get("Type") == "bind" and str(item.get("Destination", "")).startswith("/app/") for item in mounts))'
if [[ "${#dependencies[@]}" -gt 0 ]]; then
  for dependency in "${dependencies[@]}"; do
    dependency_container_id="$("${compose[@]}" ps -q "$dependency")"
    docker inspect --format '{{json .NetworkSettings.Ports}}' "$dependency_container_id" \
      | python3 -c 'import json, sys; ports = json.load(sys.stdin); bindings = [binding for values in ports.values() for binding in (values or [])]; raise SystemExit(not bindings or any(binding.get("HostIp") != "127.0.0.1" for binding in bindings))'
  done
fi

completed=1
echo "Local fixture passed: application health, development reload, source bind mount, optional dependency checks, and non-root runtime."
