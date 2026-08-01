---
name: deploy-app
description: Coordinate repository-aware application deployment work from inspection through planning, generation, hardening, validation, and operational handoff. Use when a user asks to deploy, productionize, containerize, prepare an Ubuntu VPS deployment, or create a complete Docker-based deployment rather than one isolated configuration file.
---

# Deploy App

Coordinate focused deployment skills without duplicating their technical guidance.

## Workflow

1. Read [references/workflow-selection.md](references/workflow-selection.md).
2. Invoke `analyze-deployment` before proposing or changing deployment files.
3. Present the short deployment plan and call out unsupported assumptions.
4. Select only the skills needed for the requested target.
5. Preserve existing working conventions and make the smallest safe changes.
6. Invoke `harden-deployment` before live validation.
7. Invoke `validate-deployment` at the strongest locally safe level.
8. Produce the handoff defined in [references/report-contract.md](references/report-contract.md).

## Safety gates

Proceed without extra approval for repository reads, local file generation, syntax checks, local image builds, local test containers, local logs, health checks, and non-destructive scans.

Obtain explicit approval immediately before any production connection or mutation, including image push, DNS or firewall change, service restart, production migration, TLS change, deletion, deployment, restore, or rollback. Approval for planning does not authorize execution.

Never default to broad prune commands, volume deletion, privileged containers, public Docker daemon access, hardcoded production credentials, or unverified remote scripts piped to a privileged shell.
