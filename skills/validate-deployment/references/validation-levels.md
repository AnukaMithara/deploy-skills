# Validation levels

Run levels in order and stop on a failure that makes later checks misleading.

## Level 1: structure and syntax

- Validate every skill and metadata file.
- Parse JSON and YAML where an available native tool can do so.
- Render the merged production Compose model.
- Validate Nginx syntax with placeholders or temporary test certificates.
- Check required references and scripts exist.

## Level 2: deterministic policy

- Audit secrets, image tags, privileges, networks, published ports, mounts, health checks, runtime users, and migration separation.
- Run optional Hadolint, ShellCheck, actionlint, Trivy, and Gitleaks only when installed.
- Report missing optional tools as skipped.

## Level 3: local integration

- Build the application image.
- Start dependencies and wait for readiness.
- Run migrations explicitly.
- Start the application and proxy.
- Verify database-backed application health through the public local route.
- Inspect the application runtime UID and published ports.
- Capture diagnostics on failure.
- Stop containers without deleting named volumes by default.

## Level 4: production verification

Require explicit approval before connecting. Verify host readiness, DNS, TLS, backups, deployed image identity, migrations, health, logs, and rollback readiness without overstating local evidence.
