#!/usr/bin/env python3
"""Render local Compose files and validate development workflow invariants."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


STATEFUL = ("postgres", "redis", "mysql", "mariadb", "mongo", "rabbitmq")
PROXIES = ("nginx", "caddy", "traefik")


def find_files(root: Path) -> list[Path]:
    base = next((root / name for name in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml") if (root / name).is_file()), None)
    development = next((root / name for name in ("compose.dev.yaml", "compose.dev.yml") if (root / name).is_file()), None)
    return [path for path in (base, development) if path]


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


def is_stateful(name: str, service: dict[str, Any]) -> bool:
    service_name = name.lower()
    image_name = str(service.get("image", "")).split("@", 1)[0].rsplit("/", 1)[-1].split(":", 1)[0].lower()
    return any(
        service_name == token
        or service_name.startswith(f"{token}-")
        or image_name == token
        or image_name.startswith(f"{token}-")
        for token in STATEFUL
    )


def is_proxy(name: str, service: dict[str, Any]) -> bool:
    label = f"{name} {service.get('image', '')}".lower()
    return any(token in label for token in PROXIES)


def application_service(services: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    for preferred in ("app", "api", "web"):
        if preferred in services:
            return preferred, services[preferred]
    for name, service in services.items():
        if not is_stateful(name, service) and not is_proxy(name, service) and "migrat" not in name.lower():
            return name, service
    return None


def bind_mounts(service: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in service.get("volumes", []) or [] if isinstance(item, dict) and item.get("type") == "bind"]


def command_text(service: dict[str, Any]) -> str:
    command = service.get("command", "")
    if isinstance(command, list):
        return " ".join(str(item) for item in command)
    return str(command)


def enables_development_reload(service: dict[str, Any]) -> bool:
    command = command_text(service).lower()
    markers = ("reload", "--watch", "next dev", "npm run dev", "pnpm run dev", "yarn dev", "bun run dev", "vite", "spring-boot:run")
    return any(marker in command for marker in markers)


def uses_host_reachable_network(service: dict[str, Any], networks: dict[str, Any]) -> bool:
    attached = service.get("networks")
    if not attached:
        return True
    names = attached if isinstance(attached, list) else attached.keys()
    return any(not (networks.get(name, {}) or {}).get("internal", False) for name in names)


def validate(model: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = model.get("services", {}) or {}
    networks = model.get("networks", {}) or {}
    selected = application_service(services)
    if selected is None:
        return ["no application service detected"]
    app_name, app = selected
    if not app.get("build"):
        errors.append(f"{app_name}: local application service has no build configuration")
    if not bind_mounts(app):
        errors.append(f"{app_name}: local application service has no source bind mount")
    if not enables_development_reload(app):
        errors.append(f"{app_name}: local application command does not enable reload")
    if not app.get("ports"):
        errors.append(f"{app_name}: local application has no direct host port")

    for name, service in sorted(services.items()):
        if "migrat" in name.lower() or service.get("profiles"):
            continue
        if is_proxy(name, service):
            errors.append(f"{name}: production reverse proxy appears in the local Compose model")
        if not is_stateful(name, service):
            continue
        if not service.get("healthcheck"):
            errors.append(f"{name}: dependency has no health check")
        ports = service.get("ports", []) or []
        for port in ports:
            if not isinstance(port, dict) or port.get("host_ip") != "127.0.0.1":
                errors.append(f"{name}: development dependency port is not bound to 127.0.0.1")
        if ports and not uses_host_reachable_network(service, networks):
            errors.append(f"{name}: development dependency host port is blocked by internal-only networks")
        if "postgres" in f"{name} {service.get('image', '')}".lower():
            volumes = service.get("volumes", []) or []
            if not any(isinstance(item, dict) and item.get("type") == "volume" for item in volumes):
                errors.append(f"{name}: PostgreSQL data is not assigned to a named volume")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    files = find_files(root)
    if len(files) < 2:
        print(json.dumps({"valid": False, "errors": ["base and development Compose files are required"]}, indent=2))
        return 1
    try:
        errors = validate(render(root, files))
    except (RuntimeError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"valid": not errors, "compose_files": [path.name for path in files], "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
