from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run-evals.py"


class EvaluationContractTests(unittest.TestCase):
    def test_repository_evaluation_contract_is_complete(self) -> None:
        process = subprocess.run(
            ["python3", str(RUNNER), "--root", str(ROOT)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertTrue(json.loads(process.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
