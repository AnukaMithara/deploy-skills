---
name: configure-local-compose
description: Generate or improve Docker Compose configuration for local application development with image builds, source bind mounts, framework hot reload, dependency health checks, development-only credentials, readable logs, named database volumes, and optional loopback-only database or cache ports. Use when a user requests local Docker setup, compose.dev.yaml, containerized onboarding, or hot-reload development services.
---

# Configure Local Compose

Create a repeatable development environment without leaking development behavior into production.

## Workflow

1. Require an `analyze-deployment` result or perform that analysis first.
2. Inspect existing Compose files, Dockerfiles, environment examples, and framework development commands.
3. Read [references/local-compose.md](references/local-compose.md).
4. Keep shared services in `compose.yaml` and place development-only behavior in `compose.dev.yaml`.
5. Use source bind mounts plus the framework reload command by default. Preserve the repository package manager and dependency workflow.
6. Expose the application directly for local use. Bind optional database and cache ports to loopback only.
7. Use clearly labeled development-only credentials and keep real values out of generated files.
8. Run `python3 scripts/validate_local_compose.py --root <deployment-root>` and render the merged model before reporting success.
9. Document build, migration, start, logs, stop, and safe reset commands.

Do not reuse local credentials, bind mounts, reload commands, debug ports, or direct dependency ports in production configuration. Do not delete named volumes without explicit approval.
