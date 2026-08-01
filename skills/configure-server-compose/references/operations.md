# Single-server operations

Generate an application-specific `DEPLOYMENT.md` covering the following workflow.

## Release

1. Record the currently deployed image version and rendered Compose configuration.
2. Back up state before a migration that is not demonstrably backward-compatible.
3. Pull the explicit candidate image.
4. Run the explicit migration command once.
5. Start or replace long-running services.
6. Wait for dependency and application health.
7. Verify the public route through the proxy.
8. Retain the previous version until the observation window passes.

## Backup and restore

- Identify data owner, schedule, destination, encryption, retention, and restore-test cadence.
- For PostgreSQL, use a version-compatible logical or physical method and record the server version.
- Verify backup completion and size. A created file is not proof of restorability.
- Treat restore as a destructive production action requiring explicit approval and a defined destination.

## Rollback

- Re-point the application image to the recorded previous version and render configuration before applying it.
- Do not automatically reverse a database migration. Classify it as backward-compatible, forward-fixable, or requiring a tested restore.
- Health-gate the rolled-back application and report any data compatibility risk.
- Preserve logs and failed release evidence before replacement.
