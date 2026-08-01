# Contributing

Thank you for improving Deploy Skills.

## Development workflow

1. Open an issue describing the deployment behavior or defect.
2. Keep the change focused and preserve existing public behavior unless the proposal explicitly changes it.
3. Add or update a fixture, unit test, evaluation, or deterministic invariant for every behavior change.
4. Run `./scripts/validate-all-skills.sh`, `python3 -m unittest discover -s tests -v`, and the narrowest relevant fixture validation.
5. Explain permissions, production effects, rollback behavior, and checks that were not run in the pull request.

## Skill requirements

- Keep `SKILL.md` concise and imperative.
- Put detailed or stack-specific guidance in directly linked `references/` files.
- Prefer standard-library scripts and existing repository tools.
- Do not include real credentials or example values that resemble usable secrets.
- Do not make production-changing commands the default path.
- Require explicit approval for destructive or production actions.
- Preserve existing application and deployment conventions unless they are demonstrably unsafe.

Changes to executable scripts or operational commands require a security review and at least one maintainer approval.
