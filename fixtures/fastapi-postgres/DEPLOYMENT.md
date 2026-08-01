# FastAPI fixture deployment runbook

This fixture demonstrates generated output. Replace every placeholder and verify it against the real application before using the pattern on a server.

## Required configuration

- `APP_IMAGE`: registry image name.
- `APP_VERSION`: immutable release tag; never `latest`.
- `POSTGRES_DB` and `POSTGRES_USER`: database identity.
- `POSTGRES_PASSWORD`: value from the selected server secret store.
- `DATABASE_URL`: application connection URL using the same secret.
- `HTTP_PORT`: host HTTP port; use `80` after host and firewall review.

Keep real values in a protected server environment file outside version control.

## Deploy

Production actions require explicit approval.

1. Record the current `APP_VERSION` and save `docker compose ... config` output.
2. Create and verify a PostgreSQL backup before any incompatible migration.
3. Pull the explicit candidate image.
4. Run `docker compose -f compose.yaml -f compose.production.yaml --profile tools run --rm migrate` once.
5. Run `docker compose -f compose.yaml -f compose.production.yaml up -d app db proxy`.
6. Wait for healthy services and request `/health` through Nginx.
7. Inspect logs and retain the previous application image during the observation window.

## Backup and restore

Use a PostgreSQL-version-compatible `pg_dump` process, send the encrypted artifact to storage outside this server, apply retention, and regularly restore into an isolated database. Check the command exit status and artifact size. Creating a file does not prove it can be restored.

A production restore is destructive. Require explicit approval, record the destination, stop conflicting writers, restore with a compatible PostgreSQL toolchain, and health-check the application before reopening traffic.

## Rollback

1. Preserve logs and record the failed release state.
2. Set `APP_VERSION` back to the recorded previous image.
3. Render and review the merged Compose configuration.
4. Recreate only the application and proxy services.
5. Verify `/health` and application behavior.

Do not automatically downgrade the database. Use a forward fix for backward-compatible migrations or execute the pre-tested restore plan after explicit approval when schema compatibility was broken.

## TLS

Confirm DNS first, validate an HTTP configuration, then obtain explicit approval before requesting certificates or changing live ports. Keep certificate files outside the repository, mount them read-only, validate `nginx -t`, test ACME renewal, and retain the last working proxy configuration for rollback.
