from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from src.experiment import run_experiment, EXPERIMENT_ID, WORKLOAD_ID, CHAPTER_NUMBER


class EvidenceSchemaTest(unittest.TestCase):
    def test_run_experiment_schema(self) -> None:
        evidence = run_experiment()

        # Top-level fields
        self.assertIsInstance(evidence, dict)
        self.assertIn("chapter", evidence)
        self.assertIn("experiment_id", evidence)
        self.assertIn("environment", evidence)
        self.assertIn("runs", evidence)

        self.assertEqual(evidence["chapter"], CHAPTER_NUMBER)
        self.assertEqual(evidence["experiment_id"], EXPERIMENT_ID)

        env = evidence["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

        runs = evidence["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 2)

        variants = {r["variant"] for r in runs}
        self.assertIn("baseline", variants)
        self.assertIn("treatment", variants)

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            self.assertEqual(run["workload_id"], WORKLOAD_ID)
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # Every metric value must be a finite JSON number (int or float).
            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} must be numeric, got {type(value)}",
                )

        # Additional logs should exist but are not strictly validated here
        self.assertIn("ticket_logs", evidence)
        self.assertIn("agent_interactions", evidence)

    def test_run_py_writes_results_file(self) -> None:
        # Ensure run.py writes to BOOKMAS_EVIDENCE_DIR/results.json using the
        # same schema as run_experiment().
        from run import main as run_main

        tmp_dir = Path("/tmp/bookmas_evidence_test")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(tmp_dir)

        run_main()

        results_path = tmp_dir / "results.json"
        self.assertTrue(results_path.exists(), "results.json was not created")

        with results_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Basic schema checks identical to those for run_experiment
        self.assertIsInstance(data, dict)
        self.assertEqual(data["chapter"], CHAPTER_NUMBER)
        self.assertEqual(data["experiment_id"], EXPERIMENT_ID)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 2)
        variants = {r["variant"] for r in runs}
        self.assertIn("baseline", variants)
        self.assertIn("treatment", variants)

        for run in runs:
            self.assertEqual(run["workload_id"], WORKLOAD_ID)
            self.assertIsInstance(run["metrics"], dict)
            for key, value in run["metrics"].items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} must be numeric, got {type(value)}",
                )

        # Clean up env var for other tests
        del os.environ["BOOKMAS_EVIDENCE_DIR"]


if __name__ == "__main__":
    unittest.main()
