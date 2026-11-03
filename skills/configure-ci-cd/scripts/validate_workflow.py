#!/usr/bin/env python3
"""Lint security invariants in workflows derived from the bundled template.

This dependency-free template linter is not a YAML parser or a proof of workflow
behavior. Run actionlint and the shell regression tests as complementary checks.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ACTION = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
FULL_SHA = re.compile(r"^[^@]+@[0-9a-fA-F]{40,64}$")
SECRET_ASSIGNMENT = re.compile(
    r"(?:PASSWORD|PASSWD|SECRET|TOKEN|PRIVATE_KEY|API_KEY|ACCESS_KEY)\s*:\s*(?!\$\{\{\s*secrets\.)[^\s#]+",
    re.IGNORECASE,
)


def finding(rule: str, message: str) -> dict[str, str]:
    return {"rule": rule, "severity": "error", "message": message}


def validate(text: str, *, require_migrations: bool = True) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    lowered = text.lower()
    if re.search(r"^\s*pull_request_target\s*:", text, re.MULTILINE):
        findings.append(finding("workflow.pull-request-target", "pull_request_target may execute untrusted repository code with elevated context"))
    for action in ACTION.findall(text):
        if action.startswith("./"):
            continue
        if not FULL_SHA.fullmatch(action):
            findings.append(finding("workflow.unpinned-action", f"Action is not pinned to a full commit SHA: {action}"))
    if not re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", text, re.MULTILINE):
        findings.append(finding("workflow.permissions", "Top-level permissions must default to contents: read"))
    if "packages: write" not in lowered:
        findings.append(finding("workflow.registry-permission", "Image publishing job does not declare packages: write"))
    required_security_actions = {
        "actions/dependency-review-action@": ("workflow.dependency-review", "Workflow has no dependency review"),
        "aquasecurity/trivy-action@": ("workflow.image-scan", "Workflow has no application image vulnerability scan"),
        "gitleaks/gitleaks-action@": ("workflow.secret-scan", "Workflow has no repository secret scan"),
    }
    for action, (rule, message) in required_security_actions.items():
        if action not in text:
            findings.append(finding(rule, message))
    if not re.search(r"^\s*workflow_dispatch\s*:", text, re.MULTILINE):
        findings.append(finding("workflow.manual-dispatch", "Production operations require workflow_dispatch"))
    if len(re.findall(r"^\s+name:\s*production\s*$", text, re.MULTILINE)) < 2:
        findings.append(finding("workflow.production-environment", "Deploy and rollback jobs must both use the production environment"))
    if "inputs.operation == 'deploy'" not in text or "inputs.operation == 'rollback'" not in text:
        findings.append(finding("workflow.operation-gates", "Deploy and rollback must be separate explicit operations"))
    if "inputs.image_version" not in text or re.search(r"(?:^|[:/])latest(?:\s|$)", lowered):
        findings.append(finding("workflow.immutable-version", "Production operations must use an explicit immutable image input and avoid latest"))
    if "curl --fail" not in lowered:
        findings.append(finding("workflow.healthcheck", "Workflow has no failing post-deployment HTTP health check"))
    if require_migrations and "--profile tools run --rm --pull always migrate" not in lowered:
        findings.append(finding("workflow.migration", "Deployment does not run the explicit one-shot migration profile"))
    if "ssh-keyscan" in lowered:
        findings.append(finding("workflow.ssh-trust", "Workflow must use reviewed known-host data instead of trusting ssh-keyscan output"))
    # Inspect the template's job blocks separately: checks elsewhere in the file
    # do not protect a production job unless it depends on them.
    jobs = dict(re.findall(r"^  ([A-Za-z0-9_-]+):\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)", text.split("\njobs:\n", 1)[-1], re.MULTILINE | re.DOTALL))
    for name in ("publish", "deploy", "rollback"):
        block = jobs.get(name, "")
        needs = re.search(r"^    needs: \[([^\]]+)\]\s*$", block, re.MULTILINE)
        if not needs or not {"validate", "supply-chain"}.issubset({item.strip() for item in needs.group(1).split(",")}):
            findings.append(finding("workflow.security-gates", f"{name} must depend on validate and supply-chain"))
        if name == "publish":
            continue
        required = (
            '[[ "$IMAGE_VERSION" =~ ^(v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9][A-Za-z0-9.-]*)?|[0-9a-f]{40})$ ]]',
            '[[ "$DEPLOY_DIRECTORY" =~ ^/[A-Za-z0-9_./-]+$ ]]',
            '[[ "$APP_IMAGE" =~ ^ghcr\\.io/[a-z0-9_./-]+$ ]]',
            '[[ "$APP_VERSION" =~ ^(v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9][A-Za-z0-9.-]*)?|[0-9a-f]{40})$ ]]',
            '[[ "$DEPLOY_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]',
            '[[ "$DEPLOY_HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]]',
        )
        if any(check not in block for check in required):
            findings.append(finding("workflow.remote-inputs", f"{name} must validate release and remote command inputs"))
        if "StrictHostKeyChecking=yes" not in block or "BatchMode=yes" not in block:
            findings.append(finding("workflow.ssh-options", f"{name} must explicitly enforce SSH trust and noninteractive authentication"))
        if "group: production-${{ github.repository }}" not in block or "cancel-in-progress: false" not in block:
            findings.append(finding("workflow.production-concurrency", f"{name} must serialize production operations without cancellation"))
    if require_migrations and "pull app migrate" not in jobs.get("deploy", ""):
        findings.append(finding("workflow.migration-image", "Deployment must refresh the migration image with the application image"))
    if SECRET_ASSIGNMENT.search(text):
        findings.append(finding("workflow.embedded-secret", "Secret-like value appears inline instead of using a GitHub secret"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, type=Path)
    parser.add_argument("--no-migrations", action="store_true", help="Validate an explicitly stateless workflow without migration commands")
    args = parser.parse_args()
    if not args.workflow.is_file():
        parser.error(f"workflow not found: {args.workflow}")
    findings = validate(args.workflow.read_text(encoding="utf-8", errors="replace"), require_migrations=not args.no_migrations)
    print(json.dumps({"workflow": str(args.workflow), "valid": not findings, "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
