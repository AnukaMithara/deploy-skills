# Production Dockerfile rules

- Use a trusted, current, stack-appropriate base and document version assumptions.
- Pin the runtime major/minor version and application dependencies through the repository lockfile.
- Separate build dependencies from runtime content when doing so reduces size or attack surface.
- Copy dependency metadata before application source to preserve cache reuse.
- Install only required runtime packages and clean package-manager caches in the same layer.
- Create a dedicated runtime user with ownership only where writes are required.
- Use exec-form `ENTRYPOINT` or `CMD` so the application receives signals directly.
- Document the internal port with `EXPOSE`; do not treat it as a firewall rule.
- Prefer orchestrator health checks when the image lacks a reliable health client.
- Copy source explicitly enough that `.env`, VCS data, tests, local caches, private keys, and build output cannot leak accidentally.
- Do not use build arguments for secrets. Use supported build secret mounts only when a build genuinely requires credentials.
- Do not rewrite a working application architecture solely to make a smaller image.

Run a real build when available. A static inspection cannot prove that native dependencies, user ownership, entry points, or health behavior work at runtime.
