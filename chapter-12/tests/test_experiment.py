import json
import os
import tempfile
import unittest


class TestExperiment(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean evidence directory for each test
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.evidence_dir = self.tmpdir.name

    def _run_experiment(self) -> str:
        # Run the main script with a temporary evidence directory
        from importlib import reload
        import sys

        # Adjust environment
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.evidence_dir

        # Ensure run.py is importable
        if "run" in sys.modules:
            reload(sys.modules["run"])
        import run  # type: ignore

        # Execute main
        run.main()

        evidence_path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(evidence_path), "results.json was not created")
        return evidence_path

    def test_evidence_schema_and_metrics(self) -> None:
        evidence_path = self._run_experiment()
        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level checks
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("chapter"), 12)
        self.assertEqual(data.get("experiment_id"), "exp-12-knowledge-layer-rag-impact-v1")
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        env = data["environment"]
        self.assertIsInstance(env.get("os"), str)
        self.assertIsInstance(env.get("python"), str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 8)  # 4 workloads * 2 variants

        # Track presence of variants per workload
        variants_by_workload = {}

        for run in runs:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ["baseline", "treatment"])
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIsInstance(run.get("success"), bool)

            workload_id = run["workload_id"]
            variants_by_workload.setdefault(workload_id, set()).add(run["variant"])

            # Metrics object must exist and contain only numeric values
            metrics = run.get("metrics")
            self.assertIsInstance(metrics, dict)
            self.assertGreater(len(metrics), 0)
            for key, value in metrics.items():
                self.assertIsInstance(
                    value, (int, float), f"Metric {key} must be numeric, got {type(value)}"
                )

            # Check presence of key metrics that are actually produced
            for expected_metric in [
                "answer_exact_match_rate",
                "answer_semantic_accuracy",
                "citation_precision",
                "citation_recall",
                "coverage_rate",
                "hallucination_rate",
                "stale_answer_rate",
                "task_completion_time_p50",
                "task_completion_time_p90",
            ]:
                self.assertIn(
                    expected_metric,
                    metrics,
                    f"Metric {expected_metric} missing from run metrics",
                )

        # Ensure each workload has both baseline and treatment runs
        for workload_id, variants in variants_by_workload.items():
            self.assertIn("baseline", variants, f"Missing baseline run for {workload_id}")
            self.assertIn("treatment", variants, f"Missing treatment run for {workload_id}")


if __name__ == "__main__":
    unittest.main()
