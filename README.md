# KPC resistance research: data starter

A beginner-friendly repository for organizing published KPC data, checking CSV files, and describing data completeness. This starter does **not** train a model, create protein sequences or mutations, optimize resistance, or rank candidates.

## Start here

Install Python 3.10 or newer. Open a terminal inside this folder, then run:

```sh
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.explore_data --input data/toy/synthetic_toy.csv --output-dir results/toy
python -m unittest discover -s tests -v
```

The starter uses only Python's standard library, so there are no third-party packages to download. Some computers use `python3` instead of `python`.

The exploration command prints a completeness report and writes `summary.json` and `missingness.csv`. The toy file contains invented record IDs and notes only. **It contains no protein sequences, MIC measurements, or resistance labels.** Blank biological fields are intentional. Toy data verifies the workflow; it cannot support research conclusions or model training.

## Load your real CSV later

1. Keep the original spreadsheet unchanged and export a working copy as CSV (UTF-8).
2. Copy the header from `data/raw/real_data_template.csv` and map your columns into it. Leave unknown information blank; never fill gaps with guesses.
3. Save the mapped file locally as `data/raw/kpc_variants.csv`.
4. Add each publication to `literature/sources_template.csv` and link rows using `source_id`. Preserve strain, assay, and interpretation context in `notes` and your source records.
5. Run:

```sh
python -m src.explore_data --input data/raw/kpc_variants.csv --output-dir results/real
```

You can also validate a file without writing any outputs:

```sh
python -m src.validate_data --input data/raw/kpc_variants.csv
```

Read `docs/data_dictionary.md` before mapping columns. The starter requires the exact listed header; extra columns are rejected so that a misspelled column cannot silently disappear. Preserve extra source columns in your original file and document your mapping. Real files use `is_synthetic=false`. A valid CSV is not necessarily a scientifically adequate dataset. No breakpoint, label, unit conversion, or missing value is inferred.

## What each component does

| Location | Purpose |
| --- | --- |
| `README.md` | Start here: setup and commands. |
| `requirements.txt` | Lists dependencies; currently none beyond Python. |
| `.gitignore` | Keeps private data, generated results, environments, and credentials out of normal Git adds. |
| `data/toy/` | Safe, explicitly synthetic demonstration CSV. |
| `data/raw/` | Original/local real-data location and empty schema template. |
| `data/processed/` | Placeholder for later documented, cleaned data; this starter does not transform data. |
| `literature/` | Template to record where every research observation came from. |
| `src/load_data.py` | Reads CSV text into rows without changing biological values. |
| `src/validate_data.py` | Checks headers, IDs, metadata, and explicitly entered field formats. |
| `src/explore_data.py` | Reports row counts and missing fields; writes descriptive outputs. |
| `notebooks/` | Empty starting notebook for future exploration after validation. |
| `tests/` | Small automated checks for loading, validation, and report generation. |
| `docs/` | Data definitions, provenance workflow, limits, and next steps. |
| `results/` | Generated reports; ignored by Git except its README. |

`src` means source code. `X` would eventually mean numerical inputs derived from verified sequences; `y` would mean independently supported outcome labels. Neither is created here. Sequence embeddings and classifiers require a separate research design and are not implemented in this starter.

## Put this on GitHub

Create an empty GitHub repository, then run from this folder (replace YOUR-USERNAME):

```sh
git init
git add .
git status
# Review the staged files before committing.
git commit -m "Add research data starter"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/kpc-resistance-ml.git
git push -u origin main
```

Only publish data you have permission to redistribute. The ignore rules are a convenience, not an access-control system: review staged files. No software license is selected; add an appropriate license before inviting reuse. See `docs/research_workflow.md` for scientific limitations.
