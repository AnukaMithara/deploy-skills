# Changelog

All notable changes to this project will be documented here. The project follows Semantic Versioning and the Keep a Changelog format.

## [Unreleased]

### Fixed

- Gate image publication and production operations on validation and supply-chain checks.
- Reject shell syntax in remote deployment inputs, enforce reviewed SSH trust, and normalize GHCR image names.
- Refresh migration images before execution and serialize production deploy/rollback operations.
- Exercise deployment shell commands using a local SSH stub and regression-test missing safety gates.
- Report Docker-dependent unit checks as skipped when Docker is absent, while keeping CLI validators fail-closed.
- Clarify that evaluation JSON checks measure coverage/contracts rather than agent behavior.

### Added

- Initial FastAPI and PostgreSQL production deployment vertical slice.
- Local Compose skill with bind-mounted FastAPI hot reload.
- Independent FastAPI, PostgreSQL, and ephemeral Redis fixture.
- Next.js standalone production and hot-reload development fixture with patched dependency overrides.
- Node.js API and Spring Boot PostgreSQL vertical slices with explicit migrations and live fixture coverage.
- GitHub Actions CI/CD skill with pinned actions, GHCR publishing, protected deploy and rollback operations, and deterministic workflow validation.
- Executable evaluation coverage checks and pinned Hadolint, ShellCheck, Gitleaks, and Trivy CI jobs.
