#!/usr/bin/env python3
"""Audit a Docker Compose deployment using its rendered production model."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


STATEFUL_NAMES = ("postgres", "redis", "mysql", "mariadb", "mongo", "rabbitmq")
SECRET_NAME = re.compile(r"(?:PASSWORD|PASSWD|SECRET|TOKEN|PRIVATE_KEY|API_KEY|ACCESS_KEY)", re.IGNORECASE)
PLACEHOLDER = re.compile(r"^(?:\$\{|<|change[-_]?me|replace[-_]?me|example|dummy|development)", re.IGNORECASE)


def add(findings: list[dict[str, str]], rule: str, severity: str, service: str, message: str) -> None:
    findings.append({"rule": rule, "severity": severity, "service": service, "message": message})


def compose_files(root: Path) -> list[Path]:
    base = next((root / name for name in ("compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml") if (root / name).exists()), None)
    production = next((root / name for name in ("compose.production.yaml", "compose.production.yml") if (root / name).exists()), None)
    return [path for path in (base, production) if path]


def render(root: Path, files: list[Path]) -> tuple[dict[str, Any] | None, str | None]:
    if not files:
        return None, "no Compose files found"
    if not shutil.which("docker"):
        return None, "docker CLI is unavailable; rendered-model checks skipped"
    command = ["docker", "compose"]
    for path in files:
        command.extend(["-f", str(path)])
    command.extend(["--profile", "*", "config", "--format", "json"])
    process = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown Compose render failure"
        return None, detail
    try:
        return json.loads(process.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"Compose returned invalid JSON: {exc}"


def volume_source(volume: Any) -> tuple[str, str]:
    if isinstance(volume, str):
        parts = volume.split(":", 2)
        return parts[0], "bind" if parts[0].startswith(("/", ".", "~")) else "volume"
    if isinstance(volume, dict):
        return str(volume.get("source", "")), str(volume.get("type", ""))
    return "", ""


def environment_items(environment: Any) -> list[tuple[str, str]]:
    if isinstance(environment, dict):
        return [(str(key), "" if value is None else str(value)) for key, value in environment.items()]
    if isinstance(environment, list):
        items = []
        for raw in environment:
            key, _, value = str(raw).partition("=")
            items.append((key, value))
        return items
    return []


def is_stateful_service(name: str, image: str) -> bool:
    service_name = name.lower()
    image_name = image.split("@", 1)[0].rsplit("/", 1)[-1].split(":", 1)[0].lower()
    return any(
        service_name == token
        or service_name.startswith(f"{token}-")
        or image_name == token
        or image_name.startswith(f"{token}-")
        for token in STATEFUL_NAMES
    )


def interpolated_environment_keys(files: list[Path]) -> set[tuple[str, str]]:
    """Return service/key pairs whose Compose source uses variable interpolation."""
    found: set[tuple[str, str]] = set()
    for path in files:
        current_service: str | None = None
        in_environment = False
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            service_match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
            if service_match:
                current_service = service_match.group(1)
                in_environment = False
                continue
            if current_service and re.match(r"^    environment:\s*$", line):
                in_environment = True
                continue
            if in_environment and re.match(r"^    [A-Za-z0-9_.-]+:", line):
                in_environment = False
            if in_environment:
                variable_match = re.match(r"^      ([A-Za-z_][A-Za-z0-9_]*):\s*.*\$\{", line)
                if variable_match:
                    found.add((current_service, variable_match.group(1)))
    return found


def audit_model(model: dict[str, Any], interpolated: set[tuple[str, str]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    services = model.get("services", {}) or {}
    for name, service in sorted(services.items()):
        image = str(service.get("image", ""))
        stateful = is_stateful_service(name, image)
        one_shot = "migrat" in name.lower() or bool(service.get("profiles"))
        if service.get("privileged") is True:
            add(findings, "compose.privileged", "error", name, "Privileged mode is enabled")
        if service.get("network_mode") == "host":
            add(findings, "compose.host-network", "error", name, "Host network mode is enabled")
        for volume in service.get("volumes", []) or []:
            source, kind = volume_source(volume)
            if source in {"/var/run/docker.sock", "/run/docker.sock"}:
                add(findings, "compose.docker-socket", "error", name, "Docker socket is mounted")
            if kind == "bind" and (source.startswith(".") or source == str(Path.cwd())):
                add(findings, "compose.source-bind", "error", name, "Relative source bind mount appears in production")
        if stateful and service.get("ports"):
            add(findings, "compose.public-stateful-port", "error", name, "Stateful service publishes a host port")
        if image and not stateful:
            tag = image.rsplit("/", 1)[-1]
            if ":" not in tag or tag.endswith(":latest"):
                add(findings, "compose.mutable-image", "error", name, "Application image lacks an explicit immutable version")
        for key, value in environment_items(service.get("environment", {})):
            if (
                SECRET_NAME.search(key)
                and value
                and (name, key) not in interpolated
                and not value.startswith("${")
                and not PLACEHOLDER.match(value)
            ):
                add(findings, "compose.embedded-secret", "error", name, f"Secret-like variable {key} has an inline value")
        cap_add = service.get("cap_add", []) or []
        if cap_add:
            add(findings, "compose.capabilities", "warning", name, "Additional Linux capabilities are enabled")
        if not stateful and not one_shot and not service.get("healthcheck"):
            add(findings, "compose.healthcheck", "warning", name, "Long-running application service has no health check")
        if not stateful and not one_shot and not service.get("restart"):
            add(findings, "compose.restart", "warning", name, "Long-running application service has no restart policy")
    return findings


def audit_dockerfiles(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in sorted(root.rglob("Dockerfile*")):
        if not path.is_file() or any(part in {".git", "node_modules", ".venv"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        user_lines = [line.strip() for line in text.splitlines() if line.strip().upper().startswith("USER ")]
        label = path.relative_to(root).as_posix()
        if not user_lines:
            add(findings, "dockerfile.user", "warning", label, "No runtime USER instruction")
        elif user_lines[-1].split(maxsplit=1)[1].strip() in {"root", "0"}:
            add(findings, "dockerfile.root", "error", label, "Final runtime user is root")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"deployment root not found: {root}")
    files = compose_files(root)
    model, render_error = render(root, files)
    findings = audit_dockerfiles(root)
    if model is not None:
        findings.extend(audit_model(model, interpolated_environment_keys(files)))
    report = {
        "root": str(root),
        "compose_files": [path.name for path in files],
        "render_error": render_error,
        "findings": findings,
        "summary": {
            "errors": sum(item["severity"] == "error" for item in findings),
            "warnings": sum(item["severity"] == "warning" for item in findings),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if render_error and files:
        print(f"Compose render failed or was skipped: {render_error}", file=sys.stderr)
    return 1 if render_error or report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
