# Production Compose rules

- Keep reusable definitions in `compose.yaml` and server-only changes in `compose.production.yaml`.
- Render both files together during validation; never validate an override alone.
- Reference application images as `${APP_IMAGE}:${APP_VERSION}` or an equivalent immutable identifier. Reject an empty or `latest` production version.
- Do not use application source bind mounts, development commands, debug ports, or file watchers in production.
- Publish only the reverse proxy's required ports. Use `expose` or private networking for applications and stateful services.
- Assign persistent database data to a named volume or documented external storage.
- Use health checks for dependencies and the application. Startup ordering is not a substitute for retry-capable application connections.
- Make migrations an explicit one-shot command using the same versioned application image.
- Use restart policies for long-running services, not for migration jobs.
- Set `init: true` when the runtime process does not reliably reap children.
- Drop unnecessary capabilities and enable `no-new-privileges` when compatible.
- Use read-only filesystems only after documenting required writable paths.
- Put secret names in `.env.example`; keep real values in the selected server secret store or protected environment file outside version control.
- Configure bounded Docker logging or the selected host log driver.

Compose resource support varies by deployment mode. Validate that any CPU or memory setting is enforced by the actual target rather than assuming Swarm-only `deploy` behavior applies.
