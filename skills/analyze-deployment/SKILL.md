---
name: analyze-deployment
description: Inspect an application repository and produce a machine-readable stack inventory plus a concise deployment plan. Use before generating or modifying Dockerfiles, Compose files, reverse proxies, CI/CD, server configuration, migrations, backups, or other deployment artifacts, including reviews of existing deployment configuration.
---

# Analyze Deployment

Ground every deployment decision in repository evidence.

## Inspect

1. Run `python3 scripts/detect-project.py --root <repository>`.
2. Read [references/detection-rules.md](references/detection-rules.md) when a result is ambiguous or unsupported.
3. Inspect candidate manifests and existing deployment files directly before accepting inferred commands.
4. Never expose environment or secret values. Report names and sources only.
5. Treat conflicting manifests, missing lockfiles, and unknown commands as unresolved risks rather than guesses.

## Plan

Use the detector output described in [references/output-schema.md](references/output-schema.md) to present:

- target environment and supported operating system;
- application, worker, database, cache, proxy, and scheduled services;
- public entry points and internal ports;
- persistent data and required secret names;
- build, startup, migration, health, backup, and rollback strategies;
- existing files to preserve or modify;
- assumptions, conflicts, unsupported findings, and approval-gated actions.

Stop before generation when a high-impact product choice cannot be derived safely, such as the deployment target, public domain, persistent storage owner, or migration policy.
