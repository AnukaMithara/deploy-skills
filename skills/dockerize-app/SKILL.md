---
name: dockerize-app
description: Generate or minimally improve production Dockerfiles and .dockerignore files using repository-specific build and startup evidence. Use for FastAPI, general Python, Node.js, Next.js, Spring Boot, or static applications when a user requests containerization, image hardening, Dockerfile repair, or production image optimization.
---

# Dockerize App

Create an image that matches the analyzed application instead of a generic template.

## Workflow

1. Require an `analyze-deployment` result or perform that analysis first.
2. Inspect every existing Dockerfile, ignore file, lockfile, and startup declaration.
3. Read [references/dockerfile-rules.md](references/dockerfile-rules.md).
4. Read the matching stack reference: [references/python-fastapi.md](references/python-fastapi.md) for Python/FastAPI or [references/nextjs.md](references/nextjs.md) for Next.js.
5. Propose the exact files and behavior to change before editing existing configuration.
6. Generate a matching `.dockerignore`; use [assets/dockerignore.base](assets/dockerignore.base) only as a baseline and preserve required build inputs.
7. Run `python3 scripts/inspect-dockerfile.py --dockerfile <path>` and build the image when Docker is available.
8. Report the chosen base, lockfile, build stages, runtime user, command, port, health strategy, and unresolved assumptions.

Do not embed credentials, copy local environment files, install unnecessary tools in the runtime stage, or invent a startup command unsupported by the repository.
