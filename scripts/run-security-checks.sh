#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-$repository_root/fixtures/fastapi-postgres}"

export APP_IMAGE="${APP_IMAGE:-deploy-skills-security-check}"
export APP_VERSION="${APP_VERSION:-security-check}"
export POSTGRES_DB="${POSTGRES_DB:-fixture}"
export POSTGRES_USER="${POSTGRES_USER:-fixture}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-security-check-only-password}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://fixture:security-check-only-password@db:5432/fixture}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-security-check-only-cache-password}"
export REDIS_URL="${REDIS_URL:-redis://:security-check-only-cache-password@redis:6379/0}"

python3 "$repository_root/skills/dockerize-app/scripts/inspect-dockerfile.py" \
  --dockerfile "$target/Dockerfile"
python3 "$repository_root/skills/harden-deployment/scripts/audit_deployment.py" \
  --root "$target"
