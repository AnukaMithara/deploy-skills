# Security Policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for this repository. If that feature is unavailable, contact the repository owner privately through the verified contact method on their GitHub profile.

Include the affected skill or script, reproduction steps, potential impact, and whether any production system was involved. Never include live credentials, tokens, private keys, customer data, or production logs containing sensitive data.

## Supported versions

Security fixes are applied to the latest released minor version. Until the first release, only the `main` branch is supported.

## Safety model

These skills may inspect repositories and run local validation. They must require explicit user approval before connecting to production, pushing images, changing DNS or firewall rules, restarting production services, running production migrations, changing TLS, deleting resources, deploying, restoring data, or rolling back.

Scripts in this repository must be non-destructive by default, avoid unexpected network access, redact secret values, and clearly describe any external command they execute.
