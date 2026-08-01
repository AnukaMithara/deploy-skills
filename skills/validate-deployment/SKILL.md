---
name: validate-deployment
description: Validate deployment artifacts with deterministic static checks and optional local Docker integration tests. Use after Dockerfile, Compose, Nginx, environment, migration, security, or operational changes to render configuration, build images, start services, verify health and non-root execution, inspect port exposure, and report exactly what passed or remained unverified.
---

# Validate Deployment

Match validation depth to risk and available local tools.

## Workflow

1. Read [references/validation-levels.md](references/validation-levels.md).
2. Start with syntax and static checks.
3. Run `python3 scripts/validate_compose.py --root <deployment-root>` for deterministic repository invariants.
4. Build images before starting local services when Docker is available.
5. Run explicit migrations, dependency readiness, application health, runtime user, published-port, proxy, and shutdown checks.
6. Treat optional missing tools as skipped checks, not passes.
7. Preserve named volumes during ordinary cleanup unless the user explicitly authorizes deletion.
8. Report commands, exit results, observed evidence, skipped checks, assumptions, and remaining manual production actions.

Local validation does not authorize registry push, production connection, migration, deployment, restart, restore, deletion, or rollback.
