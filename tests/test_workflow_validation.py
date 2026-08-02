from __future__ import annotations

import importlib.util
import unittest
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


if __name__ == "__main__":
    unittest.main()
