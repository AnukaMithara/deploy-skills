# Local Compose rules

- Keep shared service identity, dependency topology, health checks, and named state in `compose.yaml`.
- Add image builds, source mounts, reload commands, direct application ports, and development credentials in `compose.dev.yaml`.
- Use the repository's existing Dockerfile and dependency manager. Add a development image stage only when the runtime image cannot support reload safely.
- Bind source to the image working directory and avoid mounting dependency directories from an incompatible host platform.
- Use the framework's documented reload process. Reload is not a substitute for rebuilding after dependency or system-package changes.
- Wait for PostgreSQL, Redis, and other dependencies to pass their health checks, while keeping application-level connection retries.
- Persist authoritative local database data in a named volume. Treat caches as disposable unless the application explicitly requires durability.
- Bind optional PostgreSQL and Redis host ports to `127.0.0.1`, never all interfaces.
- Use high-numbered configurable host-port defaults to reduce collisions.
- Keep logs attached to standard output and error. Do not add production log shipping to the local override.
- Stop ordinary development services without `-v`; require explicit approval before resetting named data.
- Validate the development and production merges independently so one override cannot mask unsafe behavior in the other.
