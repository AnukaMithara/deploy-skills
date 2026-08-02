# Node.js API images

- Select the Node major version from `engines`, tool-version files, existing CI, or documented runtime support; report an assumption when none exists.
- Preserve the detected package manager and use its lockfile with the frozen install command, such as `npm ci`.
- Copy manifests before source so dependency installation remains cacheable.
- Install only production dependencies in the runtime image when build tooling is unnecessary there.
- Use an exec-form command that launches Node directly or through a package script proven by `package.json`.
- Run as the base image's non-root Node user or a dedicated numeric user and make only required runtime paths writable.
- Use `node --watch` or framework reload commands only in the development target and local Compose override.
- Handle termination signals and close servers, database pools, and worker connections cleanly.
- Prefer an orchestrator health check that verifies critical dependencies without adding an otherwise unnecessary runtime client.
