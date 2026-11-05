# Contributing

## Local setup

Use Python 3.10 or newer and follow the virtual-environment instructions in the
README. The current scripts need only Python's standard library.

Work on a branch in the existing repository:

```sh
git switch -c describe-your-change
```

Keep original source files unchanged. Keep your local working source log at
`literature/sources.csv`; the template is a blank starting point.

## Check and submit a change

Run the same unit-test command used in GitHub Actions:

```sh
python -m unittest discover -s tests -v
git diff --check
git diff
git status --short
```

Stage the specific files you intend to publish. Review the staged diff, commit,
push the branch, and open a pull request:

```sh
git add path/to/changed-file
git diff --cached
git commit -m "Describe the resulting change"
git push -u origin HEAD
```

Describe the problem, resulting behavior, and checks in the pull request. Use
metadata-only synthetic fixtures for software tests. Do not add credentials,
personal information, or source material you lack permission to redistribute.

## What the automated checks cover

The workflow runs the existing CSV-loading, format-validation, and completeness
report tests. It uses read-only repository permissions and requires no secrets.
A green run checks software behavior only.

For source bookkeeping, see [source_records.md](docs/source_records.md).
