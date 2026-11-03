# Claude plugin release preparation

Deploy Skills is packaged at the repository root. `.claude-plugin/plugin.json` defines the plugin, and `.claude-plugin/marketplace.json` lists that same root plugin for local or GitHub marketplace installation. The existing `skills/` directory is discovered automatically. No skill copies, automatic hooks, MCP connections, or package installation are added.

## Candidate listing

| Field | Draft value |
| --- | --- |
| Name | `deploy-skills` |
| Display name | Deploy Skills |
| Version | `0.1.0-rc.1` |
| Author | Anuka Mithara |
| Repository | `https://github.com/AnukaMithara/deploy-skills` |
| Plugin path | Repository root; leave the portal path field empty |
| Summary | Repository-aware Docker and single-server deployment playbooks with security checks, validation, and approval-gated operations. |
| License | Apache-2.0 |
| Primary test surface | Claude Code with local filesystem, Bash, Python, and Docker tools |

The name has not been checked for availability in the directory. Because it consists of generic words, the directory may hold it for a reviewer. Settle any naming change before the first public release. This repository contains deployment templates and scripts that need local developer tools; loading skills on another Claude surface does not establish that it can execute these tools there.

## Local acceptance

1. Run `python3 scripts/validate_claude_plugin.py`, `./scripts/validate-all-skills.sh`, and the repository tests. Skipped Docker checks remain incomplete.
2. Run `claude plugin validate . --strict` with Claude Code installed. This checks the manifest; it does not replace directory validation.
3. Add this checkout with `claude plugin marketplace add /absolute/path/to/deploy-skills`, then run `claude plugin install deploy-skills@anukamithara-deploy-skills`.
4. In a disposable application checkout, confirm that all nine `/deploy-skills:<skill>` entries load. Run `/deploy-skills:analyze-deployment` against FastAPI and Next.js samples and confirm that inspection preserves existing files.
5. Request local Docker preparation and validate the generated configuration. Verify that the stateless Next.js workflow has no migration command, and that a PostgreSQL application uses the explicit migration service.
6. Test a request to deploy without credentials or production approval. Confirm that the agent prepares configuration and stops before a production connection or mutation.
7. Complete the live fixture, scanner, and agent acceptance evidence in `RELEASE_CHECKLIST.md`. Compare representative task outputs with and without the plugin. Do not treat the coverage JSON runner as behavior evaluation.

The local packaging check is intentionally dependency-free and limited to this repository's contract. Claude's authoritative CLI validation, cached installation, runtime trials, and developer-portal validation remain separate gates.

## Submission after publication is authorized

No push, listing, submission, or release is performed by these instructions alone. Once the candidate is approved, publish the reviewed files, choose a tracked branch or tag, and open https://claude.ai/directory/manage. Select a plugin bundle, enter the repository and root path, and run Validate. Confirm the name is available and fix blocking findings. Review the listing derived from the manifest and README, then answer data-handling questions based on actual behavior described in the README. Supply a monitored contact email and review the directory terms personally before submitting.

The plugin itself has no separate hosted service or data store. When invoked, the agent can read source/configuration and create deployment artifacts. Builds and scanners fetch third-party resources; generated workflows can publish images and operate a user-configured server. Disclose those capabilities rather than describing the entire workflow as offline or claiming that it never processes personal data.

Bump the manifest version for each distributed update. Keep the marketplace entry free of a duplicate version field to avoid version drift. A local pre-release manifest does not mean the candidate is publicly released or accepted by Anthropic.

## References

- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugins/publish
- https://claude.com/docs/plugins/pre-submission-checklist
- https://claude.com/docs/plugins/submit
