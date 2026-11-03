#!/usr/bin/env python3
"""Check this repository's Claude plugin packaging without external dependencies.

This is a repository preflight, not a replacement for Claude's CLI or portal.
Only tracked files are checked so local caches do not affect release checks.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from validate_skill import validate as validate_skill


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((root / '.claude-plugin/plugin.json').read_text())
        marketplace = json.loads((root / '.claude-plugin/marketplace.json').read_text())
    except (OSError, ValueError) as exc:
        return [str(exc)]
    if manifest.get('name') != 'deploy-skills':
        errors.append('plugin name must remain deploy-skills')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?', manifest.get('version', '')):
        errors.append('plugin version must be semantic versioning')
    for field in ('displayName', 'description', 'homepage', 'repository', 'license'):
        if not isinstance(manifest.get(field), str) or not manifest[field].strip():
            errors.append(f'missing manifest field: {field}')
    if not manifest.get('author', {}).get('name'):
        errors.append('author.name is required')
    for field in ('homepage', 'repository'):
        if not str(manifest.get(field, '')).startswith('https://'):
            errors.append(f'{field} must be an HTTPS URL')
    if marketplace.get('name') != 'anukamithara-deploy-skills' or not marketplace.get('owner', {}).get('name'):
        errors.append('marketplace name/owner is missing or inconsistent')
    entries = marketplace.get('plugins', [])
    if len(entries) != 1 or entries[0].get('name') != manifest.get('name') or entries[0].get('source') != './':
        errors.append('marketplace must list this root plugin exactly once')
    # Use conventional discovery. No duplicated component declarations or hidden
    # startup execution is needed by this skills-only plugin.
    for field in ('skills', 'commands', 'agents', 'hooks', 'mcpServers', 'lspServers'):
        if field in manifest:
            errors.append(f'unexpected component override: {field}')
    skills = sorted((root / 'skills').glob('*/SKILL.md'))
    if len(skills) != 9:
        errors.append('expected nine discoverable skills')
    for skill in skills:
        errors.extend(f'{skill.parent.name}: {error}' for error in validate_skill(skill.parent))
    readme = re.sub(r'```.*?```', '', (root / 'README.md').read_text(), flags=re.S)
    if len(readme.split()) < 40 or not (root / 'LICENSE').is_file():
        errors.append('README prose and LICENSE are required')
    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, text=True, check=True).stdout.split('\0')
    seen: set[str] = set()
    for name in filter(None, tracked):
        path = root / name
        if name.casefold() in seen:
            errors.append(f'case-colliding path: {name}')
        seen.add(name.casefold())
        if path.is_symlink():
            errors.append(f'symlink is not accepted in the plugin: {name}')
        if any(part in {'.DS_Store', 'Thumbs.db', 'desktop.ini', '__MACOSX'} for part in path.parts):
            errors.append(f'OS artifact: {name}')
        if path.is_file() and path.stat().st_size > 256 * 1024:
            errors.append(f'file exceeds directory text review threshold: {name}')
    return errors


if __name__ == '__main__':
    findings = validate(Path(__file__).resolve().parents[1])
    print(json.dumps({'valid': not findings, 'scope': 'repository-packaging-preflight',
                      'claude_cli_validated': False, 'directory_validated': False,
                      'errors': findings}, indent=2))
    raise SystemExit(bool(findings))
