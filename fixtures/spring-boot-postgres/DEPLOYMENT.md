# Spring Boot fixture deployment runbook

This fixture demonstrates generated output. Replace every placeholder and verify it against the real application before using the pattern on a server.

## Required configuration

- `APP_IMAGE`: GHCR or another reviewed registry image name.
- `APP_VERSION`: immutable release tag; never `latest`.
- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`: database identity and secret-store value.
- `DATABASE_URL`: JDBC connection URL for the private `db` service.
- `HTTP_PORT`: host HTTP port after host and firewall review.

Keep real values in a protected server environment file outside version control.

## Deploy

Production actions require explicit approval.

1. Record the current image version and rendered Compose configuration.
2. Create and verify a PostgreSQL backup before an incompatible migration.
3. Pull the explicit candidate image.
4. Run `docker compose -f compose.yaml -f compose.production.yaml --profile tools run --rm migrate` once. The one-shot process enables Flyway; the long-running application keeps automatic migrations disabled.
5. Start `app`, `db`, and `proxy`, then verify `/health` through Nginx.
6. Retain the previous image during the observation window.

## Backup and restore

Use PostgreSQL-version-compatible tools, encrypt and store backups outside the server, apply retention, and regularly perform an isolated restore test. A production restore is destructive and requires explicit approval, a recorded destination, and a post-restore health check.

## Rollback

Set `APP_VERSION` to the recorded previous immutable image, render and review Compose, recreate only `app` and `proxy`, and verify `/health`. Do not automatically reverse Flyway migrations; use a forward fix or an explicitly approved, pre-tested restore when compatibility was broken.

## TLS

Confirm DNS and validate HTTP first. Require explicit approval before certificate issuance or live port changes, mount certificate data read-only, run `nginx -t`, test renewal, and retain the last working proxy configuration.
