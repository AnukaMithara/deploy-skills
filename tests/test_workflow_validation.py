from __future__ import annotations

import importlib.util
import unittest
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills/configure-ci-cd/scripts/validate_workflow.py"
WORKFLOW = ROOT / "skills/configure-ci-cd/assets/deploy.yml"


class WorkflowValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("validate_workflow", VALIDATOR)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load workflow validator")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_reference_workflow_passes(self) -> None:
        self.assertEqual(self.module.validate(WORKFLOW.read_text(encoding="utf-8")), [])

    def test_mutable_action_and_unsafe_ssh_trust_are_rejected(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        text = text.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@v7",
            1,
        ).replace("printf '%s\\n' \"$DEPLOY_KNOWN_HOSTS\"", "ssh-keyscan example.com")
        rules = {item["rule"] for item in self.module.validate(text)}
        self.assertIn("workflow.unpinned-action", rules)
        self.assertIn("workflow.ssh-trust", rules)

    def test_missing_supply_chain_checks_are_rejected(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        text = text.replace("actions/dependency-review-action@", "actions/removed-dependency-review-action@")
        text = text.replace("aquasecurity/trivy-action@", "aquasecurity/removed-trivy-action@")
        text = text.replace("gitleaks/gitleaks-action@", "gitleaks/removed-gitleaks-action@")
        rules = {item["rule"] for item in self.module.validate(text)}
        self.assertTrue(
            {"workflow.dependency-review", "workflow.image-scan", "workflow.secret-scan"}.issubset(rules)
        )


    def test_security_dependencies_are_required_for_each_release_job(self) -> None:
        text = WORKFLOW.read_text()
        for job in ("publish", "deploy", "rollback"):
            with self.subTest(job=job):
                start = text.index(f"  {job}:\n")
                changed = text[:start] + text[start:].replace("needs: [validate, supply-chain]", "needs: validate", 1)
                self.assertIn("workflow.security-gates", {f["rule"] for f in self.module.validate(changed)})

    def test_migration_image_refresh_is_required(self) -> None:
        text = WORKFLOW.read_text().replace("pull app migrate", "pull app")
        self.assertIn("workflow.migration-image", {f["rule"] for f in self.module.validate(text)})

    def test_stateless_workflow_can_omit_migrations_explicitly(self) -> None:
        text = WORKFLOW.read_text().replace("pull app migrate", "pull app")
        text = text.replace("--profile tools run --rm --pull always migrate", "config --quiet")
        self.assertEqual(self.module.validate(text, require_migrations=False), [])
        self.assertIn("workflow.migration", {f["rule"] for f in self.module.validate(text)})

    def test_remote_input_checks_are_required(self) -> None:
        text = WORKFLOW.read_text().replace('[[ "$APP_VERSION" =~ ^(v[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9][A-Za-z0-9.-]*)?|[0-9a-f]{40})$ ]]', 'true')
        self.assertIn("workflow.remote-inputs", {f["rule"] for f in self.module.validate(text)})

    def test_concurrent_production_operations_are_rejected(self) -> None:
        text = WORKFLOW.read_text().replace("cancel-in-progress: false", "cancel-in-progress: true")
        self.assertIn("workflow.production-concurrency", {f["rule"] for f in self.module.validate(text)})

    def run_block(self, step: str) -> str:
        text = WORKFLOW.read_text()
        block = text.split(f"      - name: {step}\n", 1)[1]
        body = block.split("        run: |\n", 1)[1]
        lines = []
        for line in body.splitlines():
            if line and not line.startswith("          "):
                break
            lines.append(line[10:] if line else "")
        return "\n".join(lines)

    def test_release_version_validation_executes(self) -> None:
        script = self.run_block("Validate release version")
        for value, expected in (("v1.2.3", True), ("a" * 40, True), ("stable", False), ("latest", False), ("", False), ("v1'; true; #", False), ("$(id)", False), ("a" * 129, False), ("v1\nbad", False)):
            with self.subTest(value=value):
                result = subprocess.run(["bash", "-eu", "-c", script], env={**os.environ, "IMAGE_VERSION": value}, capture_output=True)
                self.assertEqual(result.returncode == 0, expected)

    def test_remote_command_inputs_are_rejected_before_ssh(self) -> None:
        # Execute the actual template commands with a local SSH stub. No server
        # connection, registry access, or production operation occurs.
        for step in ("Deploy approved image", "Roll back application without reversing migrations"):
            script = self.run_block(step)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                stub = root / "ssh"
                stub.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$SSH_ARGUMENTS"\n')
                stub.chmod(0o755)
                arguments = root / "arguments"
                environment = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}", "SSH_ARGUMENTS": str(arguments), "RUNNER_TEMP": temporary,
                    "DEPLOY_HOST": "example.com", "DEPLOY_USER": "deploy", "DEPLOY_DIRECTORY": "/srv/my-app", "APP_IMAGE": "ghcr.io/Example/App", "APP_VERSION": "v1.2.3"}
                good = subprocess.run(["bash", "-eu", "-c", script], env=environment, capture_output=True)
                self.assertEqual(good.returncode, 0, good.stderr)
                command = arguments.read_text()
                self.assertIn("StrictHostKeyChecking=yes", command)
                if step == "Deploy approved image":
                    self.assertIn("pull app migrate", command)
                    self.assertIn("run --rm --pull always migrate", command)
                for key, value in (("APP_VERSION", "v1'; exit 0; #"), ("DEPLOY_DIRECTORY", "/srv/app'; exit 0; #"), ("APP_IMAGE", "ghcr.io/app'; id; #"), ("DEPLOY_USER", "-oProxyCommand=id"), ("DEPLOY_HOST", "host;id")):
                    with self.subTest(step=step, key=key):
                        arguments.unlink(missing_ok=True)
                        result = subprocess.run(["bash", "-eu", "-c", script], env={**environment, key: value}, capture_output=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertFalse(arguments.exists(), "unsafe input reached SSH")


if __name__ == "__main__":
    unittest.main()
