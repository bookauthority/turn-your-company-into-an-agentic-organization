import json
import os
import unittest
from pathlib import Path


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure run.py has been executed before tests or run it here.
        # We avoid importing run.main directly to keep side effects clear.
        evidence_dir = os.getenv("BOOKMAS_EVIDENCE_DIR", "/evidence")
        self.evidence_path = Path(evidence_dir) / "results.json"

        if not self.evidence_path.exists():
            # Attempt to run the experiment in-process.
            import run  # type: ignore

            run.main()

    def test_results_file_exists(self) -> None:
        self.assertTrue(self.evidence_path.exists(), "results.json should exist after running run.py")

    def test_results_schema_and_metrics(self) -> None:
        with self.evidence_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level fields
        self.assertIn("chapter", data)
        self.assertEqual(data["chapter"], 11)

        self.assertIn("experiment_id", data)
        self.assertEqual(data["experiment_id"], "exp-ch11-agentic-internal-services-hr-it-v1")

        self.assertIn("environment", data)
        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)

        self.assertIn("runs", data)
        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        # Collect workloads and check baseline/treatment presence
        workloads = {"wl-hr-onboarding", "wl-hr-changes-faq", "wl-it-access-requests", "wl-it-break-fix-faq"}
        seen = {w: {"baseline": False, "treatment": False} for w in workloads}

        for run in runs:
            # Required fields per run
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ["baseline", "treatment"])

            self.assertIn("workload_id", run)
            workload_id = run["workload_id"]
            self.assertIn(workload_id, workloads)

            self.assertIn("run_id", run)
            self.assertIsInstance(run["run_id"], str)

            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)

            self.assertIn("metrics", run)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)

            # Metrics must have numeric values (finite JSON numbers)
            for key, value in metrics.items():
                self.assertIsInstance(value, (int, float), f"Metric {key} should be numeric")

            seen[workload_id][run["variant"]] = True

        # Ensure each workload has at least one baseline and one treatment run
        for workload_id, presence in seen.items():
            self.assertTrue(presence["baseline"], f"Missing baseline run for {workload_id}")
            self.assertTrue(presence["treatment"], f"Missing treatment run for {workload_id}")


if __name__ == "__main__":
    unittest.main()
