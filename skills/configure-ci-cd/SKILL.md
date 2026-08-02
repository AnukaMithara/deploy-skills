---
name: configure-ci-cd
description: Generate or audit secure GitHub Actions workflows for validating deployment files, publishing immutable application images to GHCR, and running approval-gated single-server deploy or rollback operations. Use when deployment work needs CI/CD, registry publishing, protected environments, post-deployment health checks, or a manual rollback workflow.
license: Apache-2.0
---

# Configure CI/CD

Create the smallest GitHub Actions workflow that matches the repository and deployment target.

## Workflow

1. Analyze existing workflows, build commands, Compose files, migrations, health routes, and registry decisions before changing CI/CD.
2. Read [references/github-actions.md](references/github-actions.md) and preserve compatible repository conventions.
3. Use [assets/deploy.yml](assets/deploy.yml) only as a reviewed starting point; replace every repository-specific placeholder.
4. Keep pull-request validation read-only and publish only immutable release tags.
5. Gate deployment and rollback with a protected `production` environment and explicit manual inputs.
6. Keep migrations explicit, health-gate releases, and never automatically reverse a database migration.
7. Run `python3 scripts/validate_workflow.py --workflow <path>` and any available action, secret, and image scanners.
8. Report required repository variables, secrets, environment rules, validation evidence, and remaining manual setup.

Do not push images, connect to a server, deploy, migrate production data, or roll back without explicit approval at the point of action.
