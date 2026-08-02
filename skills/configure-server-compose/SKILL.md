---
name: configure-server-compose
description: Generate or improve Docker Compose configuration for production deployment on a single Ubuntu or comparable Debian-based server. Use when an application needs versioned images, internal networks, PostgreSQL persistence, health checks, explicit migrations, restart behavior, secrets guidance, backup, and rollback without development bind mounts.
license: Apache-2.0
---

# Configure Server Compose

Create server configuration that remains operationally recoverable.

## Workflow

1. Require repository analysis and a production Dockerfile decision.
2. Inspect and preserve existing Compose service names, networks, volumes, and environment names where safe.
3. Read [references/production-compose.md](references/production-compose.md).
4. Generate `compose.yaml` for shared service definitions and `compose.production.yaml` for production-only behavior.
5. Keep PostgreSQL and other stateful dependencies off host-published ports by default.
6. Use explicit versioned application images in production; do not use `latest`.
7. Make schema migration an explicit one-shot command or service, not an application startup side effect.
8. Read [references/operations.md](references/operations.md) and generate deployment, backup, restore, health, and rollback steps.
9. Render the merged model with `docker compose ... config` before reporting success.

Do not deploy, migrate production data, restore data, restart production services, or delete containers or volumes without explicit approval at the point of action.
