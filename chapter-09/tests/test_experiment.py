import json
import os
import unittest


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure the experiment has been run; if not, run it.
        # We avoid importing run as a module-level side effect.
        from run import main as run_main

        evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        self.results_path = os.path.join(evidence_dir, "results.json")
        if not os.path.exists(self.results_path):
            run_main()

    def test_results_schema(self) -> None:
        with open(self.results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIsInstance(data, dict)
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        # Chapter and experiment id
        self.assertEqual(data["chapter"], 9)
        self.assertEqual(data["experiment_id"], "exp-ch09-agentic-sales-ops-mas-vs-manual-v1")

        # Environment
        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIsInstance(env.get("os", ""), str)
        self.assertIsInstance(env.get("python", ""), str)

        # Runs
        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreater(len(runs), 0)

        by_workload = {}

        for run in runs:
            self.assertIsInstance(run, dict)
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
            self.assertIsInstance(metrics, dict)
            self.assertGreaterEqual(len(metrics), 1)

            for mk, mv in metrics.items():
                self.assertIsInstance(mk, str)
                self.assertIsInstance(mv, (int, float))

            # Track variants per workload
            by_workload.setdefault(workload_id, set()).add(variant)

        # Ensure each workload has both baseline and treatment
        for workload_id, variants in by_workload.items():
            self.assertIn("baseline", variants, msg=f"Missing baseline for {workload_id}")
            self.assertIn("treatment", variants, msg=f"Missing treatment for {workload_id}")

    def test_metrics_non_empty_and_numeric(self) -> None:
        with open(self.results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for run in data["runs"]:
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)
            self.assertGreaterEqual(len(metrics), 1)
            for value in metrics.values():
                self.assertIsInstance(value, (int, float))


if __name__ == "__main__":
    unittest.main()
