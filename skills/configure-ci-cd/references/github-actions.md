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
- Accept `vMAJOR.MINOR.PATCH` (optionally with a prerelease suffix) or a full lowercase 40-character commit SHA. Reject other tags and shell syntax. Tags are references, not digest identities: protect release tags and prevent registry tag replacement; record the resolved image digest in the handoff.
- Normalize the owner/repository image path to lowercase for GHCR.
- Require validation and supply-chain scanning to pass before publishing, deploying, or rolling back. Retain the exact image identity in the deployment report.

## Production protection

- Put deployment and rollback jobs in a GitHub Environment named `production`.
- Require maintainers to configure environment reviewers before enabling the workflow.
- Store host, user, deployment directory, known-host entry, and public health URL as environment variables or secrets according to sensitivity.
- Store the SSH private key only as an environment secret. Never generate, echo, or commit it.
- Do not use `ssh-keyscan` as a trust decision inside the workflow; require a reviewed `known_hosts` value.

## Deploy and rollback

- Validate version, host, SSH user, image path, and absolute deployment directory before constructing remote commands. The template supports DNS/IPv4 hosts and paths without spaces; adapt and test argument handling before supporting other forms.
- Explicitly enable strict host-key checking and noninteractive SSH authentication.
- Serialize deploy and rollback using the same production concurrency group, without canceling an operation already running.
- Record the previous version before deployment and back up state before an incompatible migration.
- Pull both application and migration images before running migrations. Use `run --pull always` for the one-shot migration container so a cached image cannot silently win.
- Run migrations once as a separate Compose profile before replacing long-running services. For applications without migrations, remove both `migrate` from the pull service list and the entire migration command; run the validator with `--no-migrations`.
- Verify the public health URL after replacement and preserve diagnostics on failure.
- Make rollback a separate manual action requiring the previous immutable version and the same production approval gate.
- Never automatically downgrade a database. Use a forward fix or an explicitly approved, pre-tested restore plan.

## Validation boundaries

- The bundled validator checks the structure and safety guards of this template. It does not parse arbitrary YAML, establish environment reviewer settings, or prove that a version tag is immutable.
- Execute shell regression tests to exercise accepted and rejected inputs. Use actionlint when available and run real fixture builds and health checks before release.
- `scripts/run-evals.py` validates prompt coverage and invariant-contract completeness only. It does not run a model or assess agent behavior; record separate agent trials before claiming cross-agent support.
