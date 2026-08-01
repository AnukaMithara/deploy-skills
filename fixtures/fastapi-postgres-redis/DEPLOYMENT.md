# FastAPI Redis fixture deployment runbook

This fixture demonstrates generated output. Replace every placeholder and verify it against the real application before using the pattern on a server.

## State model

PostgreSQL is authoritative and uses a named volume. Redis is a disposable cache: persistence is disabled, no Redis volume is created, and cache contents may be lost during restart or replacement. Do not store sessions or authoritative records in this Redis configuration.

## Required configuration

- `APP_IMAGE` and immutable `APP_VERSION`.
- `POSTGRES_DB`, `POSTGRES_USER`, and secret-managed `POSTGRES_PASSWORD`.
- Secret-managed `REDIS_PASSWORD` and a matching `REDIS_URL` using the internal service name.
- `HTTP_PORT`; use `80` only after host and firewall review.

Keep real values in a protected server environment file outside version control. Use separate PostgreSQL and Redis passwords.

## Deploy

Production actions require explicit approval.

1. Record the deployed image version and rendered Compose configuration.
2. Back up PostgreSQL before any incompatible migration.
3. Pull the explicit candidate image.
4. Run `docker compose -f compose.yaml -f compose.production.yaml --profile tools run --rm migrate` once.
5. Start `db`, `redis`, `app`, and `proxy` with the production merge.
6. Wait for healthy services and verify `/health` reports both dependencies reachable.
7. Retain the previous application image during the observation window.

## Backup, restore, and rollback

Back up PostgreSQL with a version-compatible process, encrypt it outside the server, and test restoration into an isolated database. Redis requires no backup in this cache-only model.

A production restore, deployment, or rollback requires explicit approval. Roll back by restoring the recorded `APP_VERSION`, rendering the merged model, recreating the application and proxy, and verifying health. Do not automatically downgrade the database; use a forward fix or the tested PostgreSQL restore plan when schema compatibility is broken.

## TLS

Confirm DNS, validate HTTP bootstrap, and obtain explicit approval before requesting certificates or changing live ports. Keep certificate material outside the repository, validate `nginx -t`, dry-run renewal, and retain the last working proxy configuration.
