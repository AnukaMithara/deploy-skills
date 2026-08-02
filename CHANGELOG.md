# Changelog

All notable changes to this project will be documented here. The project follows Semantic Versioning and the Keep a Changelog format.

## [Unreleased]

### Added

- Initial FastAPI and PostgreSQL production deployment vertical slice.
- Local Compose skill with bind-mounted FastAPI hot reload.
- Independent FastAPI, PostgreSQL, and ephemeral Redis fixture.
- Next.js standalone production and hot-reload development fixture with patched dependency overrides.
- Node.js API and Spring Boot PostgreSQL vertical slices with explicit migrations and live fixture coverage.
- GitHub Actions CI/CD skill with pinned actions, GHCR publishing, protected deploy and rollback operations, and deterministic workflow validation.
- Executable evaluation coverage checks and pinned Hadolint, ShellCheck, Gitleaks, and Trivy CI jobs.
