"""Describe completeness without imputing values or interpreting resistance."""
import argparse
import csv
import json
from pathlib import Path
from .load_data import COLUMNS, load_csv
from .validate_data import validate_rows


def summarize(rows):
    return {
        "row_count": len(rows),
        "synthetic_row_count": sum(row["is_synthetic"] == "true" for row in rows),
        "real_row_count": sum(row["is_synthetic"] == "false" for row in rows),
        "missing_by_column": {key: sum(not row[key].strip() for row in rows) for key in COLUMNS},
        "notice": "Descriptive completeness only; no biological conclusions or labels inferred.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        rows = load_csv(args.input)
        errors = validate_rows(rows)
        if errors:
            raise ValueError("\n".join(errors))
        report = summarize(rows)
        report["input_file"] = str(Path(args.input))
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        with (output / "missingness.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["column", "missing_count", "total_rows"])
            writer.writerows((key, count, len(rows)) for key, count in report["missing_by_column"].items())
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, f"Exploration failed: {exc}\n")
    print(json.dumps(report, indent=2))
    print(f"Reports saved to {output}. Existing report filenames are overwritten on reruns.")


if __name__ == "__main__":
    main()
