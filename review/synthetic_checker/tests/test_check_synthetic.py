"""Tests for check_synthetic.py, using only the committed fixtures."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_synthetic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def run(fixture):
    folder = ROOT / "fixtures" / fixture
    report, code = check_synthetic.check(
        folder / "baseline.json", folder / "variant.json",
        folder / "manifest.json")
    return report, code


class TestFixtures(unittest.TestCase):
    def test_reordered_ids_validate(self):
        report, code = run("reordered")
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "validated")
        self.assertEqual(report["n"], 5)
        self.assertAlmostEqual(report["baseline_mean"], 0.6)
        self.assertAlmostEqual(report["variant_mean"], 0.4)
        self.assertAlmostEqual(report["mean_diff"], 0.2)
        self.assertEqual(
            (report["improved"], report["worsened"], report["tied"]),
            (1, 0, 4))

    def test_mismatched_ids_block_and_name_offenders(self):
        report, code = run("mismatched")
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "diagnostic")
        offenders = {e["query_id"] for e in report["errors"]
                     if e["code"] == "id_mismatch"}
        self.assertEqual(offenders, {"syn-q05", "syn-q99"})

    def test_manifest_hash_mismatch_blocks(self):
        # Re-run the reordered fixture with a tampered manifest copy.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("baseline.json", "variant.json", "manifest.json"):
                (folder / name).write_bytes(
                    (ROOT / "fixtures" / "reordered" / name).read_bytes())
            manifest = json.loads((folder / "manifest.json").read_text())
            manifest["files"]["baseline.json"]["sha256"] = "0" * 64
            (folder / "manifest.json").write_text(json.dumps(manifest))
            report, code = check_synthetic.check(
                folder / "baseline.json", folder / "variant.json",
                folder / "manifest.json")
            self.assertEqual(code, 2)
            self.assertTrue(any(e["code"] == "manifest_hash_mismatch"
                                for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
