"""Guard the CI-matrix coverage check in python_matrix.py."""

from pathlib import Path

from .python_matrix import main, read_tested_versions, uncovered_versions


def test_reads_only_quoted_matrix_python_values(tmp_path: Path) -> None:
    """The parser picks up quoted `python:` matrix legs and ignores every `python_version:` key."""
    # --- arrange ----------------------
    workflow = tmp_path / "wf.yml"
    workflow.write_text(
        "        include:\n"
        '          - { python: "3.11", resolution: highest       }\n'
        '          - { python: "3.14", resolution: lowest-direct }\n'
        "          python_version: ${{ matrix.python }}\n",
        encoding="utf-8",
    )

    # --- act --------------------------
    tested = read_tested_versions(workflow)

    # --- assert -----------------------
    assert tested == {"3.11", "3.14"}


def test_uncovered_versions_flags_declared_gap_only() -> None:
    """A declared version absent from the matrix is uncovered; an extra matrix leg is not."""
    # --- act / assert -----------------
    assert uncovered_versions(declared={"3.11", "3.15"}, tested={"3.11", "3.14"}) == {"3.15"}


def test_uncovered_versions_accepts_exact_build_pins() -> None:
    """A leg pinned to an exact build covers its minor; a shorter minor does not match through the prefix."""
    # --- act / assert -----------------
    assert uncovered_versions(declared={"3.15"}, tested={"3.15.0rc1"}) == set()
    assert uncovered_versions(declared={"3.1"}, tested={"3.15.0rc1"}) == {"3.1"}


def test_repo_matrix_covers_declared_versions() -> None:
    """The live repo satisfies the invariant: every declared version has a matrix leg."""
    # --- act / assert -----------------
    assert main() == 0
