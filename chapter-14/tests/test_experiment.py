import json
import os
import unittest

import run as experiment_run


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary evidence directory under /tmp to avoid collisions.
        self.evidence_dir = "/tmp/bookmas_evidence_test"
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.evidence_dir

        # Run the experiment in-process.
        experiment_run.main()

        self.evidence_path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(self.evidence_path), "results.json not created")

        with open(self.evidence_path, "r", encoding="utf-8") as f:
            self.evidence = json.load(f)

    def test_top_level_schema(self):
        ev = self.evidence
        self.assertIn("chapter", ev)
        self.assertEqual(ev["chapter"], 14)
        self.assertIn("experiment_id", ev)
        self.assertEqual(ev["experiment_id"], "exp-014-operate-monitor-improve-mas-v1")
        self.assertIn("environment", ev)
        self.assertIsInstance(ev["environment"], dict)
        self.assertIn("os", ev["environment"])
        self.assertIn("python", ev["environment"])

    def test_runs_schema_and_metrics(self):
        runs = self.evidence.get("runs")
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        variants = set()
        workload_ids = set()

        for run in runs:
            # Required fields
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            variant = run["variant"]
            self.assertIn(variant, {"baseline", "treatment"})
            variants.add(variant)

            workload_ids.add(run["workload_id"])

            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            # Ensure at least one numeric metric and that all are numbers
            self.assertGreater(len(metrics), 0)
            for k, v in metrics.items():
                self.assertIsInstance(v, (int, float), msg=f"Metric {k} must be numeric")

        # Ensure at least one shared workload id
        self.assertGreater(len(workload_ids), 0)
        # Ensure both baseline and treatment are present
        self.assertIn("baseline", variants)
        self.assertIn("treatment", variants)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
