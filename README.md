# Deploy Skills

Production-ready deployment playbooks for AI coding agents.

Deploy Skills helps Codex, Claude Code, GitHub Copilot, Cursor, and other Agent Skills-compatible agents inspect an application before creating secure, validated deployment configuration. The current vertical slices cover local Docker development and single-server production for FastAPI, Node.js APIs, and Spring Boot with PostgreSQL, optional Redis caching for FastAPI, and Next.js standalone deployment.

## What the skills do

```text
Inspect -> Plan -> Generate -> Harden -> Validate -> Document
```

- Detect application structure, dependencies, ports, migrations, health endpoints, and existing deployment files.
- Generate or improve multi-stage, non-root Docker images.
- Separate shared Compose configuration from production overrides.
- Add portable local Compose overrides with source bind mounts and hot reload.
- Keep stateful services private and persistent.
- Configure Nginx and provide approval-gated TLS guidance.
- Generate pinned GitHub Actions for GHCR publishing and approval-gated deploy or rollback operations.
- Check common deployment security failures deterministically.
- Build, start, health-check, and report what was actually verified.

## Included skills

| Skill | Purpose |
| --- | --- |
| `deploy-app` | Route and coordinate a complete deployment workflow. |
| `analyze-deployment` | Inspect a repository and produce a deployment plan. |
| `dockerize-app` | Create or improve Dockerfiles and `.dockerignore`. |
| `configure-local-compose` | Create local Compose environments with hot reload. |
| `configure-server-compose` | Create production Docker Compose configuration for one server. |
| `configure-reverse-proxy` | Configure Nginx and document TLS bootstrap. |
| `configure-ci-cd` | Generate secure GitHub Actions for image publishing and approval-gated production operations. |
| `harden-deployment` | Audit deployment configuration for unsafe defaults. |
| `validate-deployment` | Run deterministic static and live deployment checks. |

## Install

Install the repository with a compatible skill installer:

```bash
npx skills add AnukaMithara/deploy-skills
```

Or install a single skill directory with your agent's skill installer. Always review executable scripts before installing a public skill.

## Example

```text
Use $deploy-app to prepare this FastAPI application for production on an Ubuntu VPS with PostgreSQL and Nginx.
```

The agent must analyze existing configuration and show a short deployment plan before it changes files. Connecting to a server, deploying, migrating production data, changing TLS, or deleting resources always requires explicit approval.

## Validate this repository

Fast checks:

```bash
./scripts/validate-all-skills.sh
gh skill publish --dry-run
python3 -m unittest discover -s tests -v
python3 scripts/run-evals.py
python3 skills/configure-ci-cd/scripts/validate_workflow.py \
  --workflow skills/configure-ci-cd/assets/deploy.yml
./scripts/run-security-checks.sh fixtures/fastapi-postgres
./scripts/run-security-checks.sh fixtures/nextjs
python3 skills/configure-local-compose/scripts/validate_local_compose.py \
  --root fixtures/fastapi-postgres-redis
APP_IMAGE=deploy-skills-fastapi APP_VERSION=fixture-test \
POSTGRES_DB=fixture POSTGRES_USER=fixture \
POSTGRES_PASSWORD=fixture-local-only-password \
DATABASE_URL=postgresql+psycopg://fixture:fixture-local-only-password@db:5432/fixture \
docker compose -f fixtures/fastapi-postgres/compose.yaml \
  -f fixtures/fastapi-postgres/compose.production.yaml config --quiet
```

Live fixture validation:

```bash
./scripts/run-fixture.sh fixtures/fastapi-postgres
./scripts/run-fixture.sh fixtures/fastapi-postgres-redis
./scripts/run-local-fixture.sh fixtures/fastapi-postgres-redis
./scripts/run-fixture.sh fixtures/nextjs
./scripts/run-local-fixture.sh fixtures/nextjs
./scripts/run-fixture.sh fixtures/node-api-postgres
./scripts/run-local-fixture.sh fixtures/node-api-postgres
./scripts/run-fixture.sh fixtures/spring-boot-postgres
./scripts/run-local-fixture.sh fixtures/spring-boot-postgres
```

The live test builds images and starts local containers. It does not connect to a remote server or delete named volumes.

## Current scope

The repository now proves FastAPI, Node.js API, Spring Boot, PostgreSQL, optional ephemeral Redis caching, and Next.js standalone output across local hot-reload and single-server production Compose. It also covers Ubuntu VPS guidance, Nginx, explicit migrations, dependency health checks, backup and rollback guidance, GHCR publishing, and approval-gated GitHub Actions deployment. Managed platforms, Kubernetes, Terraform, and Ansible remain planned.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing executable content. Report vulnerabilities through the process in [SECURITY.md](SECURITY.md), not through public issues.

Licensed under Apache-2.0.
