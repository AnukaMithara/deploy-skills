# Deployment report contract

End every completed workflow with these sections, omitting none and writing `None` or `Not verified` where appropriate:

1. Detected stack and deployment target.
2. Files created and modified.
3. Build, migration, deployment, and health commands.
4. Required environment-variable and secret names without values.
5. Public ports, internal ports, networks, and persistent volumes.
6. Startup order and health checks.
7. Backup and restore procedure.
8. Release rollback and migration-recovery procedure.
9. Security decisions and accepted exceptions.
10. Validation evidence separated into static, build, and live checks.
11. Assumptions, risks, skipped checks, and remaining manual actions.

Never summarize a skipped or unavailable check as successful. Never call local fixture validation a production deployment test.
