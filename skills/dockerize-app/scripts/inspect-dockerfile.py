#!/usr/bin/env python3
"""Inspect a Dockerfile for baseline production invariants."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def finding(rule: str, severity: str, message: str) -> dict[str, str]:
    return {"rule": rule, "severity": severity, "message": message}


def inspect(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    active = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    results: list[dict[str, str]] = []
    from_lines = [line for line in active if line.upper().startswith("FROM ")]
    if not from_lines:
        results.append(finding("dockerfile.from", "error", "Dockerfile has no FROM instruction"))
    if any(re.search(r":latest(?:\s|$)", line, re.IGNORECASE) for line in from_lines):
        results.append(finding("dockerfile.latest-base", "warning", "Base image uses the mutable latest tag"))
    user_lines = [line for line in active if line.upper().startswith("USER ")]
    if not user_lines:
        results.append(finding("dockerfile.user", "error", "Dockerfile has no runtime USER instruction"))
    elif user_lines[-1].split(maxsplit=1)[1].strip() in {"0", "root"}:
        results.append(finding("dockerfile.root", "error", "Final runtime user is root"))
    if not any(line.upper().startswith(("CMD ", "ENTRYPOINT ")) for line in active):
        results.append(finding("dockerfile.command", "error", "Dockerfile has no CMD or ENTRYPOINT"))
    for line_number, line in enumerate(active, start=1):
        if re.search(r"\b(?:PASSWORD|SECRET|TOKEN|PRIVATE_KEY|API_KEY)\s*=", line, re.IGNORECASE):
            results.append(finding("dockerfile.secret", "error", f"Secret-like assignment appears near active instruction {line_number}"))
        if line.upper().startswith("ADD ") and "http" in line.lower():
            results.append(finding("dockerfile.remote-add", "warning", "Remote ADD obscures download verification"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dockerfile", required=True, type=Path)
    args = parser.parse_args()
    if not args.dockerfile.is_file():
        parser.error(f"Dockerfile not found: {args.dockerfile}")
    findings = inspect(args.dockerfile)
    print(json.dumps({"dockerfile": str(args.dockerfile), "findings": findings}, indent=2))
    return 1 if any(item["severity"] == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
