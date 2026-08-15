"""Check that the CI test matrix covers every Python in `.python-versions`.

`scripts/release.py` checks `.python-versions` against the trove classifiers, but nothing checks it
against the hand-curated matrix in `.github/workflows/_unit_tests.yml` — so a version can be declared,
classified, pass the release check, and reach PyPI with no test leg ever running on it.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON_VERSIONS_FILE = REPO_ROOT / ".python-versions"
UNIT_TESTS_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "_unit_tests.yml"

# Matrix legs quote their Python as `python: "3.11"`. The setup step's `python_version:` key and the
# `${{ ... }}` references carry no `python:`-quoted literal, so this matches the matrix versions and
# nothing else.
_MATRIX_PYTHON = re.compile(r'\bpython:\s*"([^"]+)"')


def read_declared_versions(path: Path = PYTHON_VERSIONS_FILE) -> set[str]:
    """Return the Python minors declared in `.python-versions` (one per non-empty line)."""
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def read_tested_versions(path: Path = UNIT_TESTS_WORKFLOW) -> set[str]:
    """Return the Python value of every leg in the workflow's test matrix."""
    return set(_MATRIX_PYTHON.findall(path.read_text(encoding="utf-8")))


def uncovered_versions(declared: set[str], tested: set[str]) -> set[str]:
    """Return declared versions with no matching matrix leg; extra tested legs are allowed.

    A declared minor is covered by an exact match or by a leg pinned to a fuller version of that
    minor (`3.15` is covered by a `3.15.0rc1` leg); the dot in the prefix test keeps `3.1` from
    counting as covered by a `3.15` leg.
    """
    return {d for d in declared if not any(t == d or t.startswith(f"{d}.") for t in tested)}


def main() -> int:
    """Report any declared Python version the CI matrix does not test; return 1 if any."""
    declared = read_declared_versions()
    tested = read_tested_versions()
    missing = uncovered_versions(declared, tested)
    if missing:
        print(
            f".python-versions declares {sorted(missing)} with no matching leg in the "
            f"{UNIT_TESTS_WORKFLOW.relative_to(REPO_ROOT)} test matrix (matrix tests {sorted(tested)}).",
            file=sys.stderr,
        )
        return 1
    print(f"CI matrix covers all {len(declared)} declared Python versions: {sorted(declared)}")
    return 0
