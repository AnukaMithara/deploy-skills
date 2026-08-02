# v0.1.0 release checklist

Complete this checklist from a clean clone. Publishing, repository-setting changes, registry writes, and production operations require explicit maintainer approval.

## Portable skills

- Run `./scripts/validate-all-skills.sh` and confirm both repository validation and `gh skill publish --dry-run` pass.
- Install one skill into Codex from its GitHub directory and execute a positive trigger evaluation.
- Load the same unmodified skill in Claude Code and execute the equivalent evaluation.
- Run `python3 scripts/run-evals.py` and record the result.

## Fixtures and security

- Run the full unit suite and all production and local fixture scripts listed in `README.md`.
- Confirm every production application runs as non-root, every stateful port remains private, and every public health route passes through Nginx.
- Confirm Hadolint, ShellCheck, Gitleaks, and Trivy pass in GitHub Actions; do not treat a locally unavailable tool as a pass.
- Confirm no credential, certificate, environment file, production data, or generated local artifact is included in the release diff.

## Repository protection

- Require pull requests, maintainer review for executable changes, and the repository CI checks on `main`.
- Enable secret scanning, push protection, dependency review, and security advisories where the hosting plan supports them.
- Protect tags matching `v*` against deletion and modification before publishing the first release.
- Configure the `production` environment with required reviewers before enabling any generated deployment workflow.

## Release

- Update `CHANGELOG.md`, the supported-stack table, and known limitations from observed results.
- Create the signed `v0.1.0` tag only after every acceptance criterion is evidenced.
- Publish release notes and installation examples, then retain failures as regression fixtures.
