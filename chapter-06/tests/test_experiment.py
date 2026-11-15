import json
import os
import unittest


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence directory.
        self.evidence_dir = "/evidence"
        os.makedirs(self.evidence_dir, exist_ok=True)
        # Run the experiment once for the tests to consume its output.
        # Importing run.py and calling main keeps things simple.
        import run as experiment_run

        experiment_run.main()

    def test_results_json_exists_and_is_valid(self) -> None:
        path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(path), "results.json must be created")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level schema checks.
        self.assertIn("chapter", data)
        self.assertEqual(data["chapter"], 6)
        self.assertIn("experiment_id", data)
        self.assertIsInstance(data["experiment_id"], str)
        self.assertIn("environment", data)
        self.assertIsInstance(data["environment"], dict)
        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)

        # At least one baseline and one treatment run per workload.
        variants_by_workload = {}
        for run in data["runs"]:
            self.assertIn("variant", run)
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIn("metrics", run)

            self.assertIsInstance(run["variant"], str)
            self.assertIsInstance(run["workload_id"], str)
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)
            self.assertIsInstance(run["metrics"], dict)

            # Metrics must all be finite numbers.
            for key, value in run["metrics"].items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric {key} must be numeric, got {type(value)}",
                )

            wl = run["workload_id"]
            variants_by_workload.setdefault(wl, set()).add(run["variant"])

        for wl, variants in variants_by_workload.items():
            self.assertIn(
                "baseline",
                variants,
                msg=f"Workload {wl} must have a baseline run",
            )
            self.assertIn(
                "treatment",
                variants,
                msg=f"Workload {wl} must have a treatment run",
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
