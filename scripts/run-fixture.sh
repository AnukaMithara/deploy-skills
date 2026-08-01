#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="${1:-$repository_root/fixtures/fastapi-postgres}"
fixture_name="$(basename "$fixture")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for live fixture validation." >&2
  exit 2
fi

if [[ "$fixture_name" == *redis* ]]; then
  export APP_IMAGE="deploy-skills-fastapi-redis"
  export HTTP_PORT="${HTTP_PORT:-18081}"
else
  export APP_IMAGE="deploy-skills-fastapi"
  export HTTP_PORT="${HTTP_PORT:-18080}"
fi
export APP_VERSION="fixture-test"
export POSTGRES_DB="fixture"
export POSTGRES_USER="fixture"
export POSTGRES_PASSWORD="fixture-local-only-password"
export DATABASE_URL="postgresql+psycopg://fixture:fixture-local-only-password@db:5432/fixture"
export REDIS_PASSWORD="fixture-local-only-cache-password"
export REDIS_URL="redis://:fixture-local-only-cache-password@redis:6379/0"

compose=(docker compose -f "$fixture/compose.yaml" -f "$fixture/compose.production.yaml")
completed=0
health_file="$(mktemp -t deploy-skills-health.XXXXXX)"

cleanup() {
  if [[ "$completed" -ne 1 ]]; then
    "${compose[@]}" logs --no-color --tail=200 || true
  fi
  "${compose[@]}" down --remove-orphans || true
  rm -f "$health_file"
}
trap cleanup EXIT

docker build --tag "$APP_IMAGE:$APP_VERSION" "$fixture"
"${compose[@]}" config --quiet
python3 "$repository_root/skills/validate-deployment/scripts/validate_compose.py" --root "$fixture"
services="$("${compose[@]}" --profile '*' config --services)"
dependencies=(db)
if grep -qx redis <<<"$services"; then
  dependencies+=(redis)
fi
"${compose[@]}" up -d "${dependencies[@]}"
"${compose[@]}" --profile tools run --rm migrate
"${compose[@]}" up -d app proxy

healthy=0
for _attempt in $(seq 1 45); do
  if curl --fail --silent "http://127.0.0.1:$HTTP_PORT/health" > "$health_file"; then
    healthy=1
    break
  fi
  sleep 2
done
if [[ "$healthy" -ne 1 ]]; then
  echo "Fixture did not become healthy." >&2
  exit 1
fi

grep -q '"database":"reachable"' "$health_file"
if grep -qx redis <<<"$services"; then
  grep -q '"redis":"reachable"' "$health_file"
fi
runtime_uid="$("${compose[@]}" exec -T app id -u)"
if [[ "$runtime_uid" == "0" ]]; then
  echo "Application container runs as root." >&2
  exit 1
fi
db_container_id="$("${compose[@]}" ps -q db)"
if docker inspect --format '{{json .NetworkSettings.Ports}}' "$db_container_id" \
  | python3 -c 'import json, sys; ports = json.load(sys.stdin); raise SystemExit(any(value for value in ports.values()))'; then
  :
else
  echo "PostgreSQL unexpectedly publishes a host port." >&2
  exit 1
fi
if grep -qx redis <<<"$services"; then
  redis_container_id="$("${compose[@]}" ps -q redis)"
  if docker inspect --format '{{json .NetworkSettings.Ports}}' "$redis_container_id" \
    | python3 -c 'import json, sys; ports = json.load(sys.stdin); raise SystemExit(any(value for value in ports.values()))'; then
    :
  else
    echo "Redis unexpectedly publishes a host port." >&2
    exit 1
  fi
fi
"${compose[@]}" exec -T proxy nginx -t

completed=1
echo "Fixture passed: dependency health, migration, non-root runtime, private stateful ports, and Nginx syntax."
