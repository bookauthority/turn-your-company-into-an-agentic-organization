import json
import os
import unittest

from workflow_common import WORKLOAD_IDS


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure run.py has been executed; in this sandbox we assume
        # the test runner invokes python run.py beforehand, but we
        # also tolerate pre-existing evidence.
        self.evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        self.results_path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(self.results_path), f"Expected evidence file at {self.results_path}")
        with open(self.results_path, "r", encoding="utf-8") as f:
            self.evidence = json.load(f)

    def test_top_level_schema(self) -> None:
        ev = self.evidence
        self.assertIsInstance(ev, dict)
        self.assertIn("chapter", ev)
        self.assertIn("experiment_id", ev)
        self.assertIn("environment", ev)
        self.assertIn("runs", ev)
        self.assertEqual(ev["chapter"], 7)
        self.assertEqual(ev["experiment_id"], "ch7-durable-workflows-approvals-exceptions-v1")
        self.assertIsInstance(ev["environment"], dict)
        self.assertIn("os", ev["environment"])
        self.assertIn("python", ev["environment"])
        self.assertIsInstance(ev["runs"], list)
        self.assertGreaterEqual(len(ev["runs"]), 1)

    def test_runs_structure_and_metrics(self) -> None:
        runs = self.evidence["runs"]
        # Track presence of variants per workload
        seen = {wid: {"baseline": 0, "treatment": 0} for wid in WORKLOAD_IDS}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIn(workload_id, WORKLOAD_IDS)

            seen[workload_id][variant] += 1

            self.assertIsInstance(run["success"], bool)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            self.assertGreaterEqual(len(metrics), 1)

            for k, v in metrics.items():
                # metric values must be finite numbers
                self.assertIsInstance(v, (int, float), msg=f"Metric {k} is not numeric")

        # Ensure at least one baseline and one treatment run per workload
        for wid in WORKLOAD_IDS:
            self.assertGreaterEqual(seen[wid]["baseline"], 1, f"No baseline run for {wid}")
            self.assertGreaterEqual(seen[wid]["treatment"], 1, f"No treatment run for {wid}")


if __name__ == "__main__":
    unittest.main()
