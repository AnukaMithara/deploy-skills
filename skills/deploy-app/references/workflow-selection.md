# Workflow selection

Select the smallest set of skills that covers the request.

| Request | Required sequence |
| --- | --- |
| Full production deployment | analyze -> dockerize -> server Compose -> reverse proxy when public -> CI/CD when requested -> harden -> validate |
| Dockerfile only | analyze -> dockerize -> validate |
| Local Docker development | analyze -> dockerize -> local Compose -> validate |
| Production Compose only | analyze -> server Compose -> harden -> validate |
| Security review | analyze existing files -> harden -> targeted validation |
| GitHub deployment automation | analyze existing workflows -> CI/CD -> harden -> validate |
| Deployment failure | collect evidence first; do not rewrite configuration speculatively |

Do not load unrelated stack or provider guidance. When a user asks only for review, stop after findings unless they also authorize changes.

Use repository evidence in this precedence order:

1. Existing deployment and operations documentation.
2. Lockfiles and executable build/start declarations.
3. Framework configuration and application entry points.
4. Existing Docker, Compose, proxy, and CI/CD behavior.
5. Inference, labeled explicitly.

If evidence conflicts, preserve the conflict in the plan and ask before choosing a behavior that affects production data, public traffic, or availability.
