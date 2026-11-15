import json
import os
import sys
import types
import unittest


class TestChapter10Experiment(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence directory exists
        self.evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)

    def _run_module(self, module_name: str) -> None:
        """Import and run a module's main block if present.

        We avoid subprocesses; instead, we import run.py as a module and
        invoke its main() function directly.
        """
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # Import the module dynamically
            spec = None
            try:
                spec = __import__(module_name)
            except ModuleNotFoundError as exc:  # pragma: no cover - defensive
                self.fail(f"Could not import module {module_name}: {exc}")
            module = spec
        # If module exposes main(), call it; otherwise rely on import side effects
        if hasattr(module, "main") and isinstance(getattr(module, "main"), types.FunctionType):
            module.main()

    def test_run_produces_valid_evidence(self) -> None:
        # Execute the experiment via run.py
        # Ensure project root is on sys.path
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        # Import and call run.main()
        import run as run_module  # type: ignore

        if hasattr(run_module, "main"):
            run_module.main()

        # Load evidence JSON
        evidence_path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(evidence_path), "results.json not created")

        with open(evidence_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level schema checks
        self.assertIsInstance(data, dict)
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["chapter"], 10)

        self.assertIsInstance(data["experiment_id"], str)
        self.assertEqual(data["experiment_id"], "exp-ch10-finance-ap-procurement-v1")

        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 8)  # 4 workloads * 2 variants

        # Collect workload/variant coverage
        coverage = {}
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

            # Verify all metric values are numbers (no bools, no None)
            self.assertGreaterEqual(len(metrics), 1)
            for k, v in metrics.items():
                self.assertIsInstance(k, str)
                # bool is subclass of int; explicitly reject
                self.assertFalse(isinstance(v, bool))
                self.assertIsInstance(v, (int, float))

            key = (workload_id, variant)
            coverage[key] = coverage.get(key, 0) + 1

        # Require at least one baseline and one treatment run per workload
        expected_workloads = {
            "dataset-invoices-v1",
            "dataset-pos-v1",
            "dataset-recon-v1",
            "dataset-spend-v1",
        }
        for wid in expected_workloads:
            self.assertIn((wid, "baseline"), coverage, f"Missing baseline run for {wid}")
            self.assertIn((wid, "treatment"), coverage, f"Missing treatment run for {wid}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
