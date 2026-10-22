"""Read CSV values as text, preserving blanks and source strings."""
import csv
from pathlib import Path

COLUMNS = ("record_id", "variant_id", "protein_sequence", "mic_value", "mic_unit",
           "resistance_label", "source_id", "is_synthetic", "notes")


def load_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("CSV header must be exactly: " + ",".join(COLUMNS))
        rows = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV record {line}: wrong number of fields")
            rows.append(row)
    return rows
