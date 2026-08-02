# GitHub Actions deployment rules

## Events and permissions

- Run read-only validation for pull requests and branch pushes.
- Publish images only for an intentional immutable release tag or an explicit user-approved dispatch.
- Declare top-level `contents: read`; grant `packages: write` only to the image-publishing job.
- Avoid `pull_request_target` for workflows that build or execute repository code.
- Pin every third-party action to a full commit SHA and retain the release tag in a comment for reviewability.

## Image publication

- Default to `ghcr.io/<owner>/<repository>` when the project has no existing registry decision.
- Authenticate with `GITHUB_TOKEN`; do not create a separate long-lived registry password when it is unnecessary.
- Tag application images with a release version or commit SHA. Never deploy `latest`.
- Build and test before publishing, and retain the exact image identity in the deployment report.

## Production protection

- Put deployment and rollback jobs in a GitHub Environment named `production`.
- Require maintainers to configure environment reviewers before enabling the workflow.
- Store host, user, deployment directory, known-host entry, and public health URL as environment variables or secrets according to sensitivity.
- Store the SSH private key only as an environment secret. Never generate, echo, or commit it.
- Do not use `ssh-keyscan` as a trust decision inside the workflow; require a reviewed `known_hosts` value.

## Deploy and rollback

- Accept an explicit immutable image version and reject empty or `latest` values.
- Record the previous version before deployment and back up state before an incompatible migration.
- Run migrations once as a separate Compose profile before replacing long-running services.
- Verify the public health URL after replacement and preserve diagnostics on failure.
- Make rollback a separate manual action requiring the previous immutable version and the same production approval gate.
- Never automatically downgrade a database. Use a forward fix or an explicitly approved, pre-tested restore plan.
