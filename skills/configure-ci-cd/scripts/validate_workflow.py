#!/usr/bin/env python3
"""Validate security and release invariants in a generated GitHub Actions workflow."""

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


def validate(text: str) -> list[dict[str, str]]:
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
    if "--profile tools run --rm migrate" not in lowered:
        findings.append(finding("workflow.migration", "Deployment does not run the explicit one-shot migration profile"))
    if "ssh-keyscan" in lowered:
        findings.append(finding("workflow.ssh-trust", "Workflow must use reviewed known-host data instead of trusting ssh-keyscan output"))
    if SECRET_ASSIGNMENT.search(text):
        findings.append(finding("workflow.embedded-secret", "Secret-like value appears inline instead of using a GitHub secret"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, type=Path)
    args = parser.parse_args()
    if not args.workflow.is_file():
        parser.error(f"workflow not found: {args.workflow}")
    findings = validate(args.workflow.read_text(encoding="utf-8", errors="replace"))
    print(json.dumps({"workflow": str(args.workflow), "valid": not findings, "findings": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
