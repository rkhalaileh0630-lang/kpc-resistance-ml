import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from src.load_data import COLUMNS, load_csv
from src.validate_data import validate_rows
from src.explore_data import summarize

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "data/toy/synthetic_toy.csv"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_csv(TOY)

    def test_toy_is_explicitly_synthetic_and_biologically_empty(self):
        self.assertEqual(validate_rows(self.rows), [])
        self.assertEqual(len(self.rows), 3)
        for row in self.rows:
            self.assertEqual(row["is_synthetic"], "true")
            for field in ("protein_sequence", "mic_value", "mic_unit", "resistance_label"):
                self.assertEqual(row[field], "")

    def test_duplicate_and_missing_provenance_rejected(self):
        self.rows[1]["record_id"] = self.rows[0]["record_id"]
        self.rows[0]["source_id"] = ""
        errors = " ".join(validate_rows(self.rows))
        self.assertIn("duplicate record_id", errors)
        self.assertIn("source_id is required", errors)

    def test_bad_flag_and_unpaired_mic_rejected(self):
        self.rows[0].update(is_synthetic="yes", mic_value="source text")
        errors = " ".join(validate_rows(self.rows))
        self.assertIn("is_synthetic", errors)
        self.assertIn("mic_unit", errors)

    def test_missing_values_are_not_imputed(self):
        report = summarize(self.rows)
        self.assertEqual(report["missing_by_column"]["resistance_label"], 3)
        self.assertEqual(self.rows[0]["resistance_label"], "")
        self.assertTrue(validate_rows([]))

    def test_header_and_ragged_rows_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            for content in ("wrong,header\n", ",".join(COLUMNS) + "\nshort,row\n",
                            ",".join(COLUMNS) + "\n" + ",".join(["x"] * 10) + "\n"):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    load_csv(path)

    def test_cli_writes_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            completed = subprocess.run([sys.executable, "-m", "src.explore_data", "--input", str(TOY),
                                        "--output-dir", folder], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((Path(folder) / "summary.json").read_text())
            self.assertEqual(report["row_count"], 3)
            with (Path(folder) / "missingness.csv").open() as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), len(COLUMNS))

    def test_invalid_cli_fails_without_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            path.write_text(",".join(COLUMNS) + "\n")
            output = Path(folder) / "reports"
            completed = subprocess.run([sys.executable, "-m", "src.explore_data", "--input", str(path),
                                        "--output-dir", str(output)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
