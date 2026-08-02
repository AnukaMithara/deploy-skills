#!/usr/bin/env python3
"""Validate the portable subset used by Deploy Skills skill directories."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        raw, _body = content[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    values: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid frontmatter line: {line}")
        values[key.strip()] = value.strip().strip("\"").strip("'")
    return values


def validate(skill: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        return ["SKILL.md is missing"]
    content = skill_file.read_text(encoding="utf-8")
    try:
        metadata = frontmatter(content)
    except ValueError as exc:
        return [str(exc)]
    expected = skill.name
    if metadata.get("name") != expected:
        errors.append(f"name must match directory: {expected}")
    if not NAME.fullmatch(metadata.get("name", "")):
        errors.append("name must use lowercase letters, digits, and single hyphens")
    if not {"name", "description"}.issubset(metadata) or set(metadata) - {"name", "description", "license"}:
        errors.append("frontmatter must contain name and description, with optional license")
    if metadata.get("license") not in {None, "Apache-2.0"}:
        errors.append("license must be Apache-2.0 when declared")
    description = metadata.get("description", "")
    if not description or len(description) > 1024:
        errors.append("description must contain 1 to 1024 characters")
    if "TODO" in content:
        errors.append("SKILL.md contains TODO text")
    if len(content.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    for target in LINK.findall(content):
        if target.startswith(("http://", "https://", "#")):
            continue
        resolved = (skill / target.split("#", 1)[0]).resolve()
        if not resolved.exists():
            errors.append(f"linked resource does not exist: {target}")

    openai = skill / "agents" / "openai.yaml"
    if not openai.is_file():
        errors.append("agents/openai.yaml is missing")
    else:
        agent_text = openai.read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            if key not in agent_text:
                errors.append(f"agents/openai.yaml is missing {key[:-1]}")
        if f"${expected}" not in agent_text:
            errors.append("default_prompt must reference the skill with $skill-name")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    args = parser.parse_args()
    errors = validate(args.skill.resolve())
    if errors:
        for error in errors:
            print(f"ERROR {args.skill}: {error}")
        return 1
    print(f"OK {args.skill}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
