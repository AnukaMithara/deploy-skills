---
name: harden-deployment
description: Audit Dockerfiles and Docker Compose deployment configuration for unsafe production defaults. Use before deployment or during security review to detect root containers, privileged mode, host networking, Docker socket mounts, public databases, embedded secrets, mutable application tags, unsafe bind mounts, excess capabilities, and missing health or restart controls.
---

# Harden Deployment

Find concrete unsafe configuration and propose the smallest compatible correction.

## Workflow

1. Run `python3 scripts/audit_deployment.py --root <deployment-root>`.
2. Read [references/security-rules.md](references/security-rules.md) before interpreting exceptions.
3. Verify each finding against the rendered Compose model and application needs.
4. Prioritize exploitable exposure and credential leakage over cosmetic hardening.
5. Preserve explicit application requirements when risk is documented and accepted.
6. Re-run the audit after corrections and report remaining findings by severity.

Do not claim that a static audit proves runtime isolation. Keep scanner evidence separate from build, startup, and host-level verification.
