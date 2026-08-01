#!/usr/bin/env python3
"""Inspect a repository and emit a secret-safe deployment inventory as JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".next",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
    "venv",
    "__pycache__",
}
PROJECT_MARKERS = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}
LOCKFILES = {
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lock": "bun",
    "bun.lockb": "bun",
    "gradle.lockfile": "gradle",
}
DEPLOYMENT_NAMES = {
    "compose.yaml": "compose",
    "compose.yml": "compose",
    "docker-compose.yaml": "compose",
    "docker-compose.yml": "compose",
    "nginx.conf": "proxy",
    "Caddyfile": "proxy",
    "DEPLOYMENT.md": "documentation",
}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt"}
SENSITIVE_WORDS = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "PRIVATE", "API_KEY", "ACCESS_KEY")


def relative(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    return value or "."


def walk_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".cache"))
        for name in sorted(files):
            yield Path(current) / name


def safe_text(path: Path, limit: int = 1_000_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def dependency_names_from_pyproject(path: Path) -> list[str]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    dependencies: list[str] = []
    project = data.get("project", {})
    dependencies.extend(project.get("dependencies", []) or [])
    optional = project.get("optional-dependencies", {}) or {}
    for values in optional.values():
        dependencies.extend(values or [])
    poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
    dependencies.extend(poetry.keys())
    return [str(item).lower() for item in dependencies]


def dependency_names_from_requirements(path: Path) -> list[str]:
    names: list[str] = []
    for raw in safe_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "-")):
            continue
        names.append(re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].lower())
    return names


def package_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def classify_project(directory: Path, root: Path, file_names: set[str]) -> tuple[dict[str, Any], list[str]]:
    manifests = sorted(name for name in file_names if name in PROJECT_MARKERS or name.startswith("requirements"))
    lockfiles = sorted(name for name in file_names if name in LOCKFILES)
    languages: set[str] = set()
    frameworks: set[str] = set()
    package_managers: set[str] = {LOCKFILES[name] for name in lockfiles}
    commands: dict[str, list[dict[str, str]]] = {"build": [], "start": [], "migration": [], "worker": []}
    warnings: list[str] = []
    dependency_tokens: list[str] = []

    pyproject = directory / "pyproject.toml"
    requirement_files = sorted(directory.glob("requirements*.txt"))
    if pyproject.exists() or requirement_files:
        languages.add("python")
        if not package_managers:
            package_managers.add("pip")
        dependency_tokens.extend(dependency_names_from_pyproject(pyproject) if pyproject.exists() else [])
        for requirements in requirement_files:
            dependency_tokens.extend(dependency_names_from_requirements(requirements))
        joined = " ".join(dependency_tokens)
        if "fastapi" in joined:
            frameworks.add("fastapi")
        if "django" in joined:
            frameworks.add("django")
        if (directory / "alembic.ini").exists() or (directory / "alembic").is_dir():
            commands["migration"].append({"command": "alembic upgrade head", "source": "alembic configuration"})

    node_manifest = directory / "package.json"
    if node_manifest.exists():
        languages.add("javascript")
        data = package_json(node_manifest)
        all_dependencies = {
            **(data.get("dependencies", {}) or {}),
            **(data.get("devDependencies", {}) or {}),
        }
        dependency_tokens.extend(str(name).lower() for name in all_dependencies)
        scripts = data.get("scripts", {}) or {}
        runner = next(iter(sorted(package_managers & {"npm", "pnpm", "yarn", "bun"})), "npm")
        for kind, script_name in (("build", "build"), ("start", "start")):
            if script_name in scripts:
                commands[kind].append({"command": f"{runner} run {script_name}", "source": "package.json"})
        for script_name in ("migrate", "db:migrate", "migration:run"):
            if script_name in scripts:
                commands["migration"].append({"command": f"{runner} run {script_name}", "source": "package.json"})
        if "next" in all_dependencies:
            frameworks.add("nextjs")
        if "@nestjs/core" in all_dependencies:
            frameworks.add("nestjs")

    build_files = {"pom.xml", "build.gradle", "build.gradle.kts"} & file_names
    if build_files:
        languages.add("java")
        build_text = " ".join(safe_text(directory / name) for name in sorted(build_files)).lower()
        if "spring-boot" in build_text or "org.springframework.boot" in build_text:
            frameworks.add("spring-boot")
        if "pom.xml" in build_files:
            package_managers.add("maven")
            commands["build"].append({"command": "./mvnw package", "source": "pom.xml"})
        else:
            package_managers.add("gradle")
            commands["build"].append({"command": "./gradlew build", "source": "Gradle build"})

    if len(package_managers & {"npm", "pnpm", "yarn", "bun"}) > 1:
        warnings.append(f"conflicting Node.js lockfiles in {relative(directory, root)}")
    if languages and not lockfiles and "pip" not in package_managers:
        warnings.append(f"no recognized lockfile in {relative(directory, root)}")

    return {
        "path": relative(directory, root),
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "manifests": [relative(directory / name, root) for name in manifests],
        "lockfiles": [relative(directory / name, root) for name in lockfiles],
        "package_managers": sorted(package_managers),
        "commands": commands,
        "ports": [],
        "health_endpoints": [],
    }, warnings


def collect_environment(files: list[Path], root: Path) -> list[dict[str, Any]]:
    results: dict[tuple[str, str], dict[str, Any]] = {}
    env_call = re.compile(r"(?:getenv|environ\.get)\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]")
    env_index = re.compile(r"environ\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]\s*\]")
    for path in files:
        if path.name in {".env.example", "example.env"} or path.name.endswith(".env.example"):
            for line in safe_text(path).splitlines():
                match = re.match(r"\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=", line)
                if match:
                    name = match.group(1)
                    key = (name, relative(path, root))
                    results[key] = {"name": name, "source": key[1], "sensitive": any(word in name for word in SENSITIVE_WORDS)}
        elif path.suffix in SOURCE_SUFFIXES:
            text = safe_text(path, limit=300_000)
            for name in set(env_call.findall(text) + env_index.findall(text)):
                key = (name, relative(path, root))
                results[key] = {"name": name, "source": key[1], "sensitive": any(word in name for word in SENSITIVE_WORDS)}
    return sorted(results.values(), key=lambda item: (item["name"], item["source"]))


def enrich_python_projects(projects: list[dict[str, Any]], files: list[Path], root: Path) -> None:
    for project in projects:
        if "python" not in project["languages"]:
            continue
        directory = root if project["path"] == "." else root / project["path"]
        for path in files:
            if path.suffix != ".py" or path.parent != directory and directory not in path.parents:
                continue
            text = safe_text(path, limit=300_000)
            for endpoint in sorted(set(re.findall(r"@\w+\.(?:get|head)\(\s*['\"]([^'\"]*health[^'\"]*)['\"]", text, re.IGNORECASE))):
                item = {"path": endpoint, "source": relative(path, root)}
                if item not in project["health_endpoints"]:
                    project["health_endpoints"].append(item)
            for port in sorted(set(re.findall(r"(?:port\s*=|--port(?:=|\s+))\s*(\d{2,5})", text))):
                item = {"port": int(port), "source": relative(path, root)}
                if item not in project["ports"]:
                    project["ports"].append(item)


def detect_dependencies(files: list[Path], root: Path) -> list[dict[str, str]]:
    found: dict[str, str] = {}
    patterns = {
        "postgresql": ("postgres", "psycopg", "asyncpg", "jdbc:postgresql"),
        "redis": ("redis://", "redis", "ioredis"),
    }
    candidates = [p for p in files if p.name in PROJECT_MARKERS or p.name.startswith("requirements") or "compose" in p.name.lower()]
    for path in candidates:
        text = safe_text(path, limit=500_000).lower()
        for dependency, tokens in patterns.items():
            if dependency not in found and any(token in text for token in tokens):
                found[dependency] = relative(path, root)
    return [{"type": name, "source": source} for name, source in sorted(found.items())]


def deployment_files(files: list[Path], root: Path) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for path in files:
        kind = DEPLOYMENT_NAMES.get(path.name)
        lowered = path.name.lower()
        if path.name.startswith("Dockerfile"):
            kind = "dockerfile"
        elif "compose" in lowered and path.suffix in {".yaml", ".yml"}:
            kind = "compose"
        elif ".github/workflows" in path.as_posix() and path.suffix in {".yaml", ".yml"}:
            kind = "workflow"
        if kind:
            results.append({"path": relative(path, root), "type": kind})
    return sorted(results, key=lambda item: item["path"])


def inspect(root: Path) -> dict[str, Any]:
    files = list(walk_files(root))
    by_directory: dict[Path, set[str]] = {}
    for path in files:
        by_directory.setdefault(path.parent, set()).add(path.name)

    projects: list[dict[str, Any]] = []
    warnings: list[str] = []
    for directory, names in sorted(by_directory.items(), key=lambda item: item[0].as_posix()):
        if not (names & PROJECT_MARKERS or any(name.startswith("requirements") for name in names)):
            continue
        project, project_warnings = classify_project(directory, root, names)
        if project["languages"]:
            projects.append(project)
            warnings.extend(project_warnings)

    enrich_python_projects(projects, files, root)
    if not projects:
        warnings.append("no supported project manifest detected")

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "projects": projects,
        "dependencies": detect_dependencies(files, root),
        "environment": collect_environment(files, root),
        "deployment_files": deployment_files(files, root),
        "assumptions": [],
        "warnings": sorted(set(warnings)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Repository root to inspect")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"unreadable repository root: {root}"}), file=sys.stderr)
        return 2
    try:
        print(json.dumps(inspect(root), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # defensive boundary for machine-readable callers
        print(json.dumps({"error": f"inspection failed: {type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
