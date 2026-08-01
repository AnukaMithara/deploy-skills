from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DETECTOR = ROOT / "skills/analyze-deployment/scripts/detect-project.py"
FIXTURE = ROOT / "fixtures/fastapi-postgres"
REDIS_FIXTURE = ROOT / "fixtures/fastapi-postgres-redis"
NEXTJS_FIXTURE = ROOT / "fixtures/nextjs"


class DetectProjectTests(unittest.TestCase):
    def run_detector(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(DETECTOR), "--root", str(root)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_fastapi_postgres_fixture(self) -> None:
        process = self.run_detector(FIXTURE)
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(report["schema_version"], "1.0")
        self.assertIn("fastapi", report["projects"][0]["frameworks"])
        self.assertIn("postgresql", {item["type"] for item in report["dependencies"]})
        self.assertIn("alembic upgrade head", {item["command"] for item in report["projects"][0]["commands"]["migration"]})
        self.assertIn("/health", {item["path"] for item in report["projects"][0]["health_endpoints"]})
        environment = {item["name"]: item for item in report["environment"]}
        self.assertTrue(environment["POSTGRES_PASSWORD"]["sensitive"])
        self.assertNotIn("replace-with-secret-store-value", process.stdout)

    def test_conflicting_node_lockfiles_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text('{"scripts":{"start":"node index.js"}}')
            (root / "package-lock.json").write_text("{}")
            (root / "yarn.lock").write_text("")
            process = self.run_detector(root)
            report = json.loads(process.stdout)
            self.assertTrue(any("conflicting Node.js lockfiles" in item for item in report["warnings"]))

    def test_redis_fixture_detects_cache_without_values(self) -> None:
        process = self.run_detector(REDIS_FIXTURE)
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        self.assertIn("redis", {item["type"] for item in report["dependencies"]})
        self.assertIn("REDIS_URL", {item["name"] for item in report["environment"]})
        self.assertNotIn("redis://redis:6379/0", process.stdout)

    def test_nextjs_fixture_detects_framework_commands_and_health(self) -> None:
        process = self.run_detector(NEXTJS_FIXTURE)
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        project = report["projects"][0]
        self.assertIn("nextjs", project["frameworks"])
        self.assertEqual(project["package_managers"], ["npm"])
        self.assertIn("npm run build", {item["command"] for item in project["commands"]["build"]})
        self.assertIn("npm run start", {item["command"] for item in project["commands"]["start"]})
        self.assertIn("/api/health", {item["path"] for item in project["health_endpoints"]})

    def test_missing_root_uses_contract_exit_code(self) -> None:
        process = self.run_detector(ROOT / "does-not-exist")
        self.assertEqual(process.returncode, 2)
        self.assertIn("unreadable repository root", process.stderr)


if __name__ == "__main__":
    unittest.main()
