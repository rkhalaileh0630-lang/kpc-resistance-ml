"""Validate format only; never derive scientific labels or measurements."""
import argparse
from .load_data import load_csv


def validate_rows(rows):
    errors = []
    seen = set()
    if not rows:
        errors.append("CSV has no data rows")
    for line, row in enumerate(rows, start=2):
        def error(message):
            errors.append(f"CSV record {line}: {message}")
        for field in ("record_id", "variant_id", "source_id"):
            if not row[field].strip():
                error(f"{field} is required")
        if row["record_id"] in seen:
            error("duplicate record_id")
        seen.add(row["record_id"])
        if row["is_synthetic"] not in ("true", "false"):
            error("is_synthetic must be true or false")
        sequence = row["protein_sequence"]
        if sequence and (not sequence.isascii() or not sequence.isalpha() or sequence != sequence.upper()):
            error("protein_sequence must be uppercase ASCII letters or blank")
        if bool(row["mic_value"].strip()) != bool(row["mic_unit"].strip()):
            error("mic_value and mic_unit must both be filled or both be blank")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    try:
        rows = load_csv(args.input)
        errors = validate_rows(rows)
        if errors:
            raise ValueError("\n".join(errors))
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, f"Validation failed: {exc}\n")
    print(f"Format checks passed for {len(rows)} rows. Scientific verification is still required.")


if __name__ == "__main__":
    main()
