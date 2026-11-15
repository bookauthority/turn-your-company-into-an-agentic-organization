import json
import os
import unittest
from pathlib import Path


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean evidence directory.
        self.evidence_dir = Path(os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence"))
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        # Run the experiment once for all tests.
        # Importing run.main here avoids circular imports during discovery.
        from run import main as run_main

        run_main()
        self.results_path = self.evidence_dir / "results.json"

    def test_results_file_exists(self) -> None:
        self.assertTrue(self.results_path.exists(), "results.json must exist in /evidence")

    def test_schema_and_metrics(self) -> None:
        with self.results_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertEqual(data["chapter"], 8)
        self.assertEqual(data["experiment_id"], "exp-ch08-cx-agentic-support-v1")

        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 4)  # at least 2 workloads x 2 variants

        # Track presence of baseline/treatment per workload
        by_workload = {}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            run_id = run["run_id"]
            success = run["success"]
            metrics = run["metrics"]

            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run_id, str)
            self.assertIsInstance(success, bool)

            # Ensure metrics is a dict of numbers
            self.assertIsInstance(metrics, dict)
            self.assertGreater(len(metrics), 0)
            for k, v in metrics.items():
                self.assertIsInstance(k, str)
                # Metrics MUST be numbers (int or float), not any other type.
                self.assertIsInstance(v, (int, float), msg=f"Metric {k} must be numeric, got {type(v)}")

            # Record presence of variants per workload
            by_workload.setdefault(workload_id, set()).add(variant)

        # Check that each workload has both baseline and treatment.
        for workload_id, variants in by_workload.items():
            self.assertIn("baseline", variants, f"Workload {workload_id} missing baseline run")
            self.assertIn("treatment", variants, f"Workload {workload_id} missing treatment run")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
