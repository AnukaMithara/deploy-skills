# Detector output schema

The detector emits one JSON document to standard output.

```json
{
  "schema_version": "1.0",
  "root": "/absolute/path",
  "projects": [],
  "dependencies": [],
  "environment": [],
  "deployment_files": [],
  "assumptions": [],
  "warnings": []
}
```

Each project includes its relative path, languages, frameworks, manifests, lockfiles, package managers, and candidate build/start/migration/worker commands. Ports and health endpoints include their evidence source.

Each environment entry includes only `name`, `source`, and `sensitive`. The detector must never emit the value.

`dependencies` describes detected service types such as PostgreSQL or Redis with evidence. `deployment_files` classifies existing Docker, Compose, proxy, workflow, and deployment documentation files.

An empty list means no evidence was found. `warnings` records conflicts and unsupported or incomplete evidence. `assumptions` is reserved for low-risk detector inference; deployment-specific assumptions belong in the human plan.

Exit `0` when inspection completes, even if warnings exist. Exit `2` for invalid arguments or an unreadable root. Exit `1` only for an unexpected detector failure.
