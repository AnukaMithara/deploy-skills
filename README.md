# Deploy Skills

Deployment playbooks for AI coding agents, with executable fixtures and safety checks.

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

### Claude Code plugin

This repository is one plugin containing all nine skills. Test the local checkout before publishing:

```bash
claude --plugin-dir /absolute/path/to/deploy-skills
```

Inside Claude Code, run `/deploy-skills:analyze-deployment` to inspect your application or `/deploy-skills:deploy-app` for the full workflow. The application repository is your working directory; the plugin directory holds the instructions and helper scripts.

To test marketplace installation from a local checkout:

```bash
claude plugin validate /absolute/path/to/deploy-skills --strict
claude plugin marketplace add /absolute/path/to/deploy-skills
claude plugin install deploy-skills@anukamithara-deploy-skills
```

After the plugin files have been published to GitHub, users can replace the local marketplace path with `AnukaMithara/deploy-skills`. The current local release candidate is not published or directory-approved. See [CLAUDE_PLUGIN.md](CLAUDE_PLUGIN.md) for submission preparation and remaining checks.

### Other compatible agents

Use your agent's skill installer with this repository or a single directory under `skills/`. The portable `SKILL.md` files and Codex metadata remain available. Review executable scripts before installing a public skill.

## Requirements and data handling

The plugin bundles instructions, text templates, and readable Python/Bash helpers. It has no startup hooks, background processes, MCP servers, telemetry, or automatic package installation. Loading it adds skills; running a skill can inspect application source, dependency manifests, deployment configuration, and environment variable names, then write deployment files and reports in the application checkout. Avoid providing production secrets or personal data in prompts or test fixtures. Your Claude account's data handling applies to content the agent reads.

Static helpers require Python 3.10 or later; shell helpers require Bash. Compose rendering and live fixture tests require Docker with Compose v2. Node.js/npm and a JDK/Maven are stack-specific tools, generally used inside the fixture build containers. Generated GitHub Actions require a GitHub repository; GHCR publishing and Ubuntu server operations require separately configured credentials, host trust, and approval.

When explicitly run, builds and scanners can fetch dependencies, images, actions, and vulnerability databases from package registries, container registries, GitHub, and scanner providers. Fixture tests start local containers, bind local ports, and create Docker images and named data volumes; they stop the fixture containers without deleting named volumes. Generated release workflows can publish images to GHCR, connect by SSH to the server you configure, run migrations, and call your health-check URL. Review generated files before enabling them. Production connections and mutations require explicit approval. The plugin supplies no hosted service or separate data store; files, logs, images, and volumes remain in the tools and accounts where you run them.

## Example

```text
Use $deploy-app to prepare this FastAPI application for production on an Ubuntu VPS with PostgreSQL and Nginx.
```

The agent must analyze existing configuration and show a short deployment plan before it changes files. Connecting to a server, deploying, migrating production data, changing TLS, or deleting resources always requires explicit approval.

## Validate this repository

Fast checks:

```bash
python3 scripts/validate_claude_plugin.py
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

The unit runner explicitly skips rendered-Compose checks when the Docker CLI is absent. These skips are not release evidence; CI requires Docker Compose before running the suite. The standalone deployment validators continue to return failure when Docker is unavailable.

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

The evaluation runner checks prompt coverage and invariant-contract completeness. It does not execute AI agents. Passing static checks alone does not establish release readiness; complete `RELEASE_CHECKLIST.md` with live fixture and agent-trial evidence.

## Current scope

The repository now proves FastAPI, Node.js API, Spring Boot, PostgreSQL, optional ephemeral Redis caching, and Next.js standalone output across local hot-reload and single-server production Compose. It also covers Ubuntu VPS guidance, Nginx, explicit migrations, dependency health checks, backup and rollback guidance, GHCR publishing, and approval-gated GitHub Actions deployment. Managed platforms, Kubernetes, Terraform, and Ansible remain planned.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing executable content. Report vulnerabilities through the process in [SECURITY.md](SECURITY.md), not through public issues.

Licensed under Apache-2.0.
