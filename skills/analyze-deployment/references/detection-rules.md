# Detection rules

Use deterministic evidence first and inspect ambiguous candidates manually.

## Supported evidence

| Area | Strong evidence |
| --- | --- |
| Python | `pyproject.toml`, `requirements*.txt`, `poetry.lock`, `uv.lock`, `Pipfile.lock` |
| FastAPI | dependency declaration plus imports or an ASGI entry point |
| Node.js | `package.json` plus npm, pnpm, Yarn, or Bun lockfile |
| Next.js | `next` dependency and build/start scripts |
| Spring Boot | Maven or Gradle build declaring Spring Boot |
| PostgreSQL | driver dependency, database URL name, Compose image, or migration configuration |
| Redis | client dependency, Redis URL name, or Compose image |
| Migration | Alembic, Django migrations, Prisma, Flyway, Liquibase, Sequelize, TypeORM, or project scripts |
| Health | route declarations, framework actuator settings, Docker health checks, or documented endpoint |

## Rules

- Report all manifests in a monorepo; do not collapse separate applications into one.
- Prefer a lockfile matching the detected package manager. Report multiple conflicting lockfiles.
- Treat scripts and container commands as candidates until their referenced entry points exist.
- Read environment key names from examples and configuration. If inspecting a local `.env`, never emit values.
- Ignore `.git`, dependency caches, virtual environments, build outputs, and generated vendor trees.
- Preserve unknowns. An unsupported framework is not a generic Python or Node application unless its build and startup behavior are clear.
