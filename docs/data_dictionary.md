# CSV data dictionary

One row represents one reported observation in its experimental context, not necessarily one unique variant. Repeated variants across sources or conditions may be legitimate; every observation needs a unique `record_id`.

| Column | Meaning and rule |
| --- | --- |
| record_id | Required unique observation ID. Assign stable local IDs. |
| variant_id | Required source-reported variant name. A name alone does not verify a sequence. |
| protein_sequence | Optional verified source sequence. Uppercase ASCII letters only; blanks allowed. The check does not establish biological validity, residue alphabet, identity, or length. Never reconstruct a sequence from a mutation name in this starter. |
| mic_value | Optional exact source text, including inequality signs. Never treat censored values such as `>...` as exact measurements. No numerical parsing is performed. |
| mic_unit | Source-reported unit; required whenever mic_value is present. No conversion is performed. |
| resistance_label | Optional exact source label. No vocabulary, clinical threshold, binary mapping, or resistance interpretation is assumed. |
| source_id | Required key to your literature source record. Existence of that record is checked manually, not by the program. |
| is_synthetic | Required literal `true` or `false`. This flag is supplied by you, not detected by the code. |
| notes | Optional context: antibiotic/combination, organism, strain, assay, conditions, provenance, caveats. |

All fields are loaded as text. Empty fields mean missing, not zero or susceptible. Strings such as `NA` are preserved as text and counted as present; map missing-value conventions explicitly in a documented working copy. The validator checks metadata presence, duplicate IDs, sequence text format, and paired MIC fields. It does not verify publications, units, label correctness, or experimental comparability. Keep real and synthetic datasets separate; the report counts both if a file mixes them.
