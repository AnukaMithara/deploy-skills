# Repository instructions

- Prefer minimal, reviewable changes and preserve existing deployment decisions unless they are unsafe.
- Never overwrite an existing deployment file before inspecting and reporting it.
- Keep `SKILL.md` files concise; move detailed stack rules into directly linked references.
- Use deterministic scripts for checks that can be mechanically verified.
- Do not add runtime dependencies to repository scripts without a documented need.
- Never commit credentials, generated certificates, local environment files, or production data.
- Require explicit approval before production connections or mutations.
- Run the narrowest relevant validation first, then broader fixture validation.
- Report validation evidence, assumptions, risks, and unverified areas honestly.
