# Research workflow and limits

1. Preserve original downloads and source spreadsheets locally. Record access date, publication identifier, and exact table/page in the literature template. Create your working source log as `literature/sources.csv` (ignored by Git).
2. Document how source columns map into the CSV header. Preserve reported sequences, units, inequality signs, and labels. Missing information stays blank. Use one observation per experimental context and preserve contextual details in notes.
3. Verify each source_id against the literature log. Record sequence accession and version if supplied, and distinguish experimentally measured observations from predictions. Resolve contradictions by returning to sources; do not silently average them.
4. Run validation, then review the completeness report. Correct transcription errors in a documented working copy. The original data remains unchanged.
5. Before any future modeling, agree with your mentor on an outcome definition, experimental comparability, sufficient data, and independent evaluation. Closely related sequences and repeated observations can leak information across train/test splits. Missing labels or sequences cannot be used as supervised examples without additional verified evidence.

This repository contains no model training, ESM downloads, embedding calculation, sequence generation, mutation design, resistance optimization, or candidate ranking. The synthetic metadata example is only a software demonstration. Passing tests validates program behavior, not a scientific hypothesis. No biological research references or measurements are supplied or invented.

Future dependencies should be added with reviewed versions and a reproducible environment once a concrete analysis is approved. No patient data or credentials belong in this public starter.
