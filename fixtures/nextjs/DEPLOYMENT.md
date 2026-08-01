# Next.js fixture deployment runbook

This fixture demonstrates generated output. Replace placeholders and verify the resulting image and configuration before using the pattern on a server.

## State model

The application is stateless. Next.js may use `.next/cache` for runtime caching, so production mounts that path as disposable memory-backed storage. No authoritative data is stored by this fixture and no backup is required.

## Required configuration

- `APP_IMAGE` and immutable `APP_VERSION`.
- `HTTP_PORT`; use `80` only after host and firewall review.
- Build-time `NEXT_PUBLIC_*` values, if the real application uses them. Treat them as public because Next.js embeds them in browser assets.
- Runtime server-only secrets, if required by the real application, supplied outside version control.

## Deploy

Production actions require explicit approval.

1. Record the deployed image version and rendered Compose configuration.
2. Build and push the immutable candidate image in CI.
3. Pull the explicit candidate image on the server.
4. Start `app` and `proxy` with the production merge.
5. Wait for both services to become healthy and verify `/api/health` through the proxy.
6. Retain the previous application image during the observation window.

## Rollback

Restore the recorded `APP_VERSION`, render the merged configuration, recreate `app` and `proxy`, and verify `/api/health`. The disposable cache requires no restoration.

## TLS

Confirm DNS, validate HTTP bootstrap, and obtain explicit approval before requesting certificates or changing live ports. Keep certificate material outside the repository, validate `nginx -t`, dry-run renewal, and retain the last working proxy configuration.
