# Deployment security rules

## Error

- Embedded credential or private key material.
- `privileged: true`, host networking, or a Docker socket mount without an explicit narrowly justified requirement.
- Publicly published PostgreSQL, Redis, or other internal data-service ports.
- Production application image tagged `latest` or lacking an explicit version.
- Development source bind mounts in production configuration.

## Warning

- Application Dockerfile lacks a non-root `USER`.
- Added Linux capabilities or unrestricted device access.
- Missing application or dependency health checks.
- Long-running service lacks a restart policy.
- Writable host bind mount without documented ownership and backup.
- Secret-looking value appears directly in Compose environment configuration.
- Unbounded local JSON logging.

## Review principles

- Inspect the merged production model because overrides can remove or introduce risk.
- Report file and rule evidence without printing secret values.
- Allow documented exceptions when the application cannot function otherwise, but state impact and compensating controls.
- Separate image configuration from runtime proof. `USER` is necessary evidence, not proof that every process and mounted path is safe.
