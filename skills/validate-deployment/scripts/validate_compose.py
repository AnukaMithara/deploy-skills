#!/usr/bin/env python3
"""Render production Compose files and validate deployment invariants."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


STATEFUL = ("postgres", "redis", "mysql", "mariadb", "mongo", "rabbitmq")


def find_files(root: Path) -> list[Path]:
    base = next((root / name for name in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml") if (root / name).is_file()), None)
    production = next((root / name for name in ("compose.production.yaml", "compose.production.yml") if (root / name).is_file()), None)
    return [path for path in (base, production) if path]


def render(root: Path, files: list[Path]) -> dict[str, Any]:
    if not shutil.which("docker"):
        raise RuntimeError("docker CLI is unavailable")
    command = ["docker", "compose"]
    for path in files:
        command.extend(["-f", str(path)])
    command.extend(["--profile", "*", "config", "--format", "json"])
    process = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "Compose render failed")
    return json.loads(process.stdout)


def port_target(raw: Any) -> int | None:
    if isinstance(raw, dict):
        value = raw.get("target")
        return int(value) if value is not None else None
    text = str(raw).split("/")[0]
    try:
        return int(text.rsplit(":", 1)[-1])
    except ValueError:
        return None


def is_stateful_service(name: str, image: str) -> bool:
    service_name = name.lower()
    image_name = image.split("@", 1)[0].rsplit("/", 1)[-1].split(":", 1)[0].lower()
    return any(
        service_name == token
        or service_name.startswith(f"{token}-")
        or image_name == token
        or image_name.startswith(f"{token}-")
        for token in STATEFUL
    )


def validate(model: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = model.get("services", {}) or {}
    if not services:
        return ["rendered Compose model contains no services"]
    for name, service in sorted(services.items()):
        stateful = is_stateful_service(name, str(service.get("image", "")))
        if stateful and service.get("ports"):
            targets = [port_target(item) for item in service.get("ports", [])]
            errors.append(f"{name}: stateful service publishes host ports {targets}")
        if service.get("privileged") is True:
            errors.append(f"{name}: privileged mode is enabled")
        if service.get("network_mode") == "host":
            errors.append(f"{name}: host network mode is enabled")
        for volume in service.get("volumes", []) or []:
            source = volume.get("source", "") if isinstance(volume, dict) else str(volume).split(":", 1)[0]
            if source in {"/var/run/docker.sock", "/run/docker.sock"}:
                errors.append(f"{name}: Docker socket is mounted")
        if not stateful and service.get("image"):
            image = str(service["image"])
            leaf = image.rsplit("/", 1)[-1]
            if ":" not in leaf or leaf.endswith(":latest"):
                errors.append(f"{name}: application image is not explicitly versioned")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    files = find_files(root)
    if len(files) < 2:
        print(json.dumps({"valid": False, "errors": ["base and production Compose files are required"]}, indent=2))
        return 1
    try:
        model = render(root, files)
        errors = validate(model)
    except (RuntimeError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"valid": not errors, "compose_files": [path.name for path in files], "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
