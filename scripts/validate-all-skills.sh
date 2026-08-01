#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="$repository_root/scripts/validate_skill.py"
status=0

while IFS= read -r skill_file; do
  skill_directory="$(dirname "$skill_file")"
  if ! python3 "$validator" "$skill_directory"; then
    status=1
  fi
  if command -v skills-ref >/dev/null 2>&1; then
    if ! skills-ref validate "$skill_directory"; then
      status=1
    fi
  fi
done < <(find "$repository_root/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort)

if command -v gh >/dev/null 2>&1 && gh skill publish --help >/dev/null 2>&1; then
  if ! gh skill publish "$repository_root" --dry-run; then
    status=1
  fi
fi

if [[ "$status" -ne 0 ]]; then
  exit "$status"
fi

echo "All skills passed repository validation."
