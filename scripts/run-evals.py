#!/usr/bin/env python3
"""Validate evaluation coverage and supported-output invariant contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MINIMUMS = {
    "positive": 3,
    "negative": 3,
    "ambiguous": 2,
    "edge": 3,
    "existing_configuration": 1,
    "failure_recovery": 1,
}
FIXTURE_CONTRACTS = {
    "fastapi-postgres": ("fastapi-postgres-production", "fastapi-postgres-local"),
    "fastapi-postgres-redis": ("fastapi-postgres-redis-production",),
    "nextjs": ("nextjs-production", "nextjs-local"),
    "node-api-postgres": ("node-api-postgres-production",),
    "spring-boot-postgres": ("spring-boot-postgres-production",),
}


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def evaluate(root: Path) -> list[str]:
    errors: list[str] = []
    prompts = load_object(root / "evals" / "prompts.json")
    invariants = load_object(root / "evals" / "expected-invariants.json")
    skills = prompts.get("skills", {})
    expected_skills = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    if set(skills) != expected_skills:
        errors.append(f"prompt skill set differs: missing={sorted(expected_skills - set(skills))}, extra={sorted(set(skills) - expected_skills)}")
    for name, cases in sorted(skills.items()):
        if not isinstance(cases, dict):
            errors.append(f"{name}: evaluation cases must be an object")
            continue
        seen: set[str] = set()
        for category, minimum in MINIMUMS.items():
            values = cases.get(category, [])
            if not isinstance(values, list) or len(values) < minimum:
                errors.append(f"{name}.{category}: expected at least {minimum} prompts")
                continue
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{name}.{category}: prompts must be non-empty strings")
                elif value in seen:
                    errors.append(f"{name}: duplicate prompt: {value}")
                seen.add(value)
    safety = prompts.get("safety", [])
    if not isinstance(safety, list) or len(safety) < 2:
        errors.append("safety: expected at least two approval and preservation cases")
    for fixture, contracts in FIXTURE_CONTRACTS.items():
        if not (root / "fixtures" / fixture).is_dir():
            errors.append(f"fixture is missing: {fixture}")
        for contract in contracts:
            value = invariants.get(contract)
            if not isinstance(value, dict) or not value.get("required") or not value.get("forbidden"):
                errors.append(f"invariant contract is incomplete: {contract}")
    workflow_contract = invariants.get("github-actions-production")
    if not isinstance(workflow_contract, dict) or not workflow_contract.get("required") or not workflow_contract.get("forbidden"):
        errors.append("invariant contract is incomplete: github-actions-production")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    try:
        errors = evaluate(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
