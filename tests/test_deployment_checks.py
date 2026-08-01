from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/fastapi-postgres"
REDIS_FIXTURE = ROOT / "fixtures/fastapi-postgres-redis"
NEXTJS_FIXTURE = ROOT / "fixtures/nextjs"
INSPECTOR = ROOT / "skills/dockerize-app/scripts/inspect-dockerfile.py"
AUDITOR = ROOT / "skills/harden-deployment/scripts/audit_deployment.py"
VALIDATOR = ROOT / "skills/validate-deployment/scripts/validate_compose.py"
LOCAL_VALIDATOR = ROOT / "skills/configure-local-compose/scripts/validate_local_compose.py"
COMPOSE_ENV = {
    "APP_IMAGE": "deploy-skills-fastapi",
    "APP_VERSION": "fixture-test",
    "POSTGRES_DB": "fixture",
    "POSTGRES_USER": "fixture",
    "POSTGRES_PASSWORD": "fixture-local-only-password",
    "DATABASE_URL": "postgresql+psycopg://fixture:fixture-local-only-password@db:5432/fixture",
    "REDIS_PASSWORD": "fixture-local-only-cache-password",
    "REDIS_URL": "redis://:fixture-local-only-cache-password@redis:6379/0",
}


class DeploymentCheckTests(unittest.TestCase):
    def run_script(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(COMPOSE_ENV)
        return subprocess.run(
            ["python3", str(script), *args],
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

    def test_fixture_dockerfiles_have_no_errors(self) -> None:
        for fixture in (FIXTURE, REDIS_FIXTURE, NEXTJS_FIXTURE):
            with self.subTest(fixture=fixture.name):
                process = self.run_script(INSPECTOR, "--dockerfile", str(fixture / "Dockerfile"))
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                report = json.loads(process.stdout)
                self.assertFalse([item for item in report["findings"] if item["severity"] == "error"])

    def test_fixture_security_audit_has_no_errors(self) -> None:
        for fixture in (FIXTURE, REDIS_FIXTURE, NEXTJS_FIXTURE):
            with self.subTest(fixture=fixture.name):
                process = self.run_script(AUDITOR, "--root", str(fixture))
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                report = json.loads(process.stdout)
                self.assertEqual(report["summary"]["errors"], 0)

    def test_fixture_compose_invariants(self) -> None:
        for fixture in (FIXTURE, REDIS_FIXTURE, NEXTJS_FIXTURE):
            with self.subTest(fixture=fixture.name):
                process = self.run_script(VALIDATOR, "--root", str(fixture))
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                self.assertTrue(json.loads(process.stdout)["valid"])

    def test_local_fixture_compose_invariants(self) -> None:
        for fixture in (FIXTURE, REDIS_FIXTURE, NEXTJS_FIXTURE):
            with self.subTest(fixture=fixture.name):
                process = self.run_script(LOCAL_VALIDATOR, "--root", str(fixture))
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                self.assertTrue(json.loads(process.stdout)["valid"])

    def test_inline_compose_secret_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "compose.yaml").write_text(
                "services:\n"
                "  db:\n"
                "    image: postgres:17-alpine\n"
                "    environment:\n"
                "      POSTGRES_PASSWORD: this-is-inline\n"
            )
            (root / "compose.production.yaml").write_text("services: {}\n")
            process = self.run_script(AUDITOR, "--root", str(root))
            self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
            report = json.loads(process.stdout)
            self.assertIn("compose.embedded-secret", {item["rule"] for item in report["findings"]})


class LocalComposeRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("validate_local_compose", LOCAL_VALIDATOR)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load local Compose validator")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def valid_model(self) -> dict:
        return {
            "services": {
                "app": {
                    "build": {"context": "."},
                    "command": ["uvicorn", "app.main:app", "--reload"],
                    "ports": [{"target": 8000, "published": "18000", "host_ip": "127.0.0.1"}],
                    "volumes": [{"type": "bind", "source": "/source/app", "target": "/app/app"}],
                },
                "db": {
                    "image": "postgres:17-alpine",
                    "healthcheck": {"test": ["CMD", "pg_isready"]},
                    "ports": [{"target": 5432, "published": "15432", "host_ip": "127.0.0.1"}],
                    "volumes": [{"type": "volume", "source": "postgres_data", "target": "/var/lib/postgresql/data"}],
                },
            }
        }

    def test_missing_source_bind_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["app"]["volumes"] = []
        self.assertTrue(any("source bind mount" in error for error in self.module.validate(model)))

    def test_missing_reload_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["app"]["command"] = ["uvicorn", "app.main:app"]
        self.assertTrue(any("enable reload" in error for error in self.module.validate(model)))

    def test_nextjs_development_command_enables_reload(self) -> None:
        model = self.valid_model()
        model["services"]["app"]["command"] = ["npm", "run", "dev"]
        self.assertFalse(any("enable reload" in error for error in self.module.validate(model)))

    def test_public_dependency_port_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["db"]["ports"][0]["host_ip"] = "0.0.0.0"
        self.assertTrue(any("127.0.0.1" in error for error in self.module.validate(model)))

    def test_missing_dependency_healthcheck_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["db"].pop("healthcheck")
        self.assertTrue(any("health check" in error for error in self.module.validate(model)))

    def test_internal_network_blocking_dependency_port_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["db"]["networks"] = {"backend": None}
        model["networks"] = {"backend": {"internal": True}}
        self.assertTrue(any("internal-only networks" in error for error in self.module.validate(model)))

    def test_production_proxy_is_rejected(self) -> None:
        model = self.valid_model()
        model["services"]["proxy"] = {"image": "nginx:1.28-alpine"}
        self.assertTrue(any("reverse proxy" in error for error in self.module.validate(model)))


if __name__ == "__main__":
    unittest.main()
