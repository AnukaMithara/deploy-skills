# Next.js images

- Confirm the installed Next.js and Node.js requirements from the lockfile before choosing an image. Next.js 16 requires Node.js 20.9 or newer.
- Preserve the repository package manager and use its frozen-lockfile install command.
- Set `output: "standalone"` when the application supports a Node.js server deployment.
- Build in a separate stage and copy `.next/standalone` plus `.next/static` into the runtime image.
- Run the generated `server.js` directly with `HOSTNAME=0.0.0.0` and `PORT` set explicitly.
- Run as a dedicated non-root user. Provide a writable `.next/cache` path when the application uses ISR or runtime fetch caching.
- Keep `NEXT_PUBLIC_*` values separate from runtime secrets: public values may be embedded during the build, while server-only secrets must remain runtime configuration.
- Use `next dev` only in the development image or Compose override. Never ship source bind mounts or development dependencies in the production image.
- Preserve `public/` when present. Do not invent it or fail a build merely because an application has no public assets.
- Call an application-owned health route. Do not treat the homepage as proof that upstream dependencies are healthy.
