"""Release driver for mpl-composite.

Run via ``make release VERSION=X.Y.Z``.  Validates state, bumps version, stamps
the versioned splash + README badges, finalizes the changelog, commits, tags,
opens a fresh Unreleased section, and pushes main + tag atomically.

Every check runs before the first write, so a failed check leaves the tree as it
was.  ``--dry-run`` runs every check and stops before the first write.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
README = REPO_ROOT / "README.md"
PYTHON_VERSIONS_FILE = REPO_ROOT / ".python-versions"
SPLASH_SCRIPT = REPO_ROOT / ".github" / "scripts" / "create_splash.sh"
SPLASH_BASE_PNG = REPO_ROOT / "images" / "splash" / "_splash_without_version.png"
SPLASH_FONT = REPO_ROOT / "images" / "splash" / "google_fonts_montserrat_bold.ttf"
SPLASH_WEBP = REPO_ROOT / "images" / "splash_with_version.webp"

PACKAGE_NAME = "mpl-composite"
CATEGORIES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
COVERAGE_BADGE_RE = re.compile(r"badge/coverage-[\d.]+%25-[a-z]+")
TESTS_BADGE_RE = re.compile(r"badge/tests-\d+-blue")


# ==================================================================================================
#  helpers
# ==================================================================================================
def run_command(cmd: list[str], **kw: object) -> str:
    """Run a subprocess and return stdout, or exit on failure."""
    # check=False is deliberate: the return code is handled below with
    # richer diagnostics than subprocess's own CalledProcessError.
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, **kw)
    if result.returncode != 0:
        sys.stderr.write(f"\n$ {' '.join(cmd)}\n")
        if result.stdout:
            sys.stderr.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.stdout


def print_step(n: int, msg: str) -> None:
    """Print a numbered step message."""
    print(f"  [{n:>2}] {msg}")


def fail_with_message(msg: str, code: int = 1) -> NoReturn:
    """Print an error and exit."""
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse and validate a semver string."""
    if not SEMVER_RE.match(version):
        fail_with_message(f"VERSION {version!r} is not in X.Y.Z form")
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def read_pyproject_version() -> str:
    """Read the current version from pyproject.toml."""
    text = PYPROJECT.read_text()
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    if not m:
        fail_with_message("Could not find version in pyproject.toml")
    return m.group(1)


def read_python_versions() -> list[str]:
    """Read supported Python versions from .python-versions."""
    return [v.strip() for v in PYTHON_VERSIONS_FILE.read_text().split() if v.strip()]


# ==================================================================================================
#  validation steps
# ==================================================================================================
def step_1_check_working_tree() -> None:
    """Validate working tree is on main and clean."""
    print_step(1, "working tree on main and clean")
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if branch != "main":
        fail_with_message(f"not on main (currently on {branch})")
    porcelain = run_command(["git", "status", "--porcelain"])
    if porcelain.strip():
        fail_with_message("working tree has uncommitted changes:\n" + porcelain)


def step_2_check_in_sync() -> None:
    """Validate main is in sync with origin."""
    print_step(2, "main in sync with origin")
    run_command(["git", "fetch", "origin", "main"])
    local = run_command(["git", "rev-parse", "HEAD"]).strip()
    remote = run_command(["git", "rev-parse", "origin/main"]).strip()
    if local != remote:
        fail_with_message(f"local main ({local[:8]}) does not match origin/main ({remote[:8]})")


def step_3_check_version_upgrade(version: str) -> None:
    """Validate VERSION is not a downgrade.

    Equal-to-current is deliberately valid: pyproject may already carry the
    target version when the release publishes the version the tree already
    declares (development cycles that never bumped in between).
    """
    print_step(3, f"VERSION {version} is not a downgrade")
    new = parse_semver(version)
    current = parse_semver(read_pyproject_version())
    if new < current:
        fail_with_message(f"VERSION {version} is lower than current {'.'.join(str(p) for p in current)}")


def step_4_check_tag_doesnt_exist(version: str) -> None:
    """Validate tag does not exist locally or on origin."""
    print_step(4, f"tag v{version} does not exist (local + remote)")
    tag = f"v{version}"
    if run_command(["git", "tag", "-l", tag]).strip():
        fail_with_message(f"tag {tag} already exists locally")
    if run_command(["git", "ls-remote", "--tags", "origin", tag]).strip():
        fail_with_message(f"tag {tag} already exists on origin")


def step_5_check_pypi_doesnt_have(version: str) -> None:
    """Validate version is not already on PyPI."""
    print_step(5, f"version {version} is not on PyPI")
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10):
            fail_with_message(f"version {version} is already published on PyPI")
    except urllib.error.HTTPError as e:
        # 404 = not published yet (the good case); any other status is a check failure.
        if e.code != 404:
            fail_with_message(f"PyPI check returned HTTP {e.code}")
    except urllib.error.URLError as e:
        # HTTPError is a subclass of URLError, so this only catches transport failures
        # (DNS, connection reset, the 10s timeout) — fail cleanly instead of a raw traceback.
        fail_with_message(f"could not reach PyPI to check {version}: {e.reason}")


def step_6_check_classifiers_match() -> None:
    """Validate Python classifiers match .python-versions."""
    print_step(6, "Python classifiers in pyproject.toml match .python-versions")
    versions = read_python_versions()
    text = PYPROJECT.read_text()
    declared = set(re.findall(r'"Programming Language :: Python :: ([\d.]+)"', text))
    expected = set(versions)
    missing = expected - declared
    extra = declared - expected
    if missing or extra:
        fail_with_message(
            f"classifiers do not match .python-versions. "
            f"Missing: {sorted(missing) or 'none'}; "
            f"Extra: {sorted(extra) or 'none'}"
        )


def step_7_check_changelog_has_entries() -> None:
    """Validate Unreleased section has at least one bullet entry."""
    print_step(7, "CHANGELOG.md '## Unreleased' has at least one entry")
    text = CHANGELOG.read_text()
    m = re.search(r"^## Unreleased\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        fail_with_message("no '## Unreleased' section in CHANGELOG.md")
    if not re.search(r"^- ", m.group(1), re.MULTILINE):
        fail_with_message("'## Unreleased' has no bullet entries")


def step_8_check_stamping_inputs() -> None:
    """Validate that the README badges and the splash inputs are in place for the release commit.

    A badge that the README no longer carries would otherwise be skipped silently by the
    substitution in `refresh_readme_badges`, leaving a stale badge in the release.
    """
    print_step(8, "README badges and splash inputs are in place for stamping")
    readme = README.read_text()
    for name, badge_re in (("coverage", COVERAGE_BADGE_RE), ("test-count", TESTS_BADGE_RE)):
        n_badges = len(badge_re.findall(readme))
        if n_badges != 1:
            fail_with_message(f"README.md must carry exactly 1 {name} badge to stamp (found {n_badges})")
    if shutil.which("magick") is None:
        fail_with_message("ImageMagick ('magick') is required to stamp the release splash but was not found")
    for path in (SPLASH_SCRIPT, SPLASH_BASE_PNG, SPLASH_FONT):
        if not path.is_file():
            fail_with_message(f"the splash cannot be stamped: {path.relative_to(REPO_ROOT)} is missing")


# Gathering the badge metrics is the last check: the fetch runs after every quick check has passed
# and before the first write. When the 'Push to Main' run for HEAD is still in progress, the step
# waits for it, because that is the usual state right after a merge, and waiting saves the
# maintainer from watching CI and re-running the release by hand.

# warn if the cumulative union exceeds this multiple of the largest single combo
TEST_COUNT_UNION_RATIO_WARN = 1.5

# how long to wait for an in-progress 'Push to Main' run on HEAD, and how often to re-check
CI_WAIT_TIMEOUT_SEC = 25 * 60
CI_POLL_INTERVAL_SEC = 30


@dataclass(frozen=True)
class BadgeMetrics:
    """A BadgeMetrics records the numbers on the README coverage and test-count badges for one release."""

    coverage_pct: float
    test_union: int


def _main_run_id_for(head_sha: str) -> str | None:
    """Return the id of the newest 'Push to Main' run for commit `head_sha`, or None if it has none.

    The lookup filters by commit: the unfiltered `gh run list` on `main` can briefly return an
    out-of-date result, which leaves out a run that exists.
    """
    out = run_command(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            "push_to_main.yml",
            "--commit",
            head_sha,
            "--limit",
            "1",
            "--json",
            "databaseId",
        ]
    )
    runs = json.loads(out)
    if runs:
        return str(runs[0]["databaseId"])
    else:
        return None


def _workflow_run_state(run_id: str) -> tuple[str, str]:
    """Return (status, conclusion) of the workflow run `run_id`; conclusion is empty until the run completes."""
    state = json.loads(run_command(["gh", "run", "view", run_id, "--json", "status,conclusion"]))
    return state["status"], state.get("conclusion") or ""


def _wait_for_main_ci(local_head: str) -> str:
    """Return the id of a successful 'Push to Main' run for `local_head`, waiting for one in progress.

    Aborts when:

    - no run exists for `local_head` (the push did not trigger CI);
    - the run concluded without success;
    - `CI_WAIT_TIMEOUT_SEC` passes without the run completing.

    Once found, the run is polled by its id, so an out-of-date result from `gh run list` cannot
    hide the run.
    """
    run_id = _main_run_id_for(local_head)
    if run_id is None:
        fail_with_message(f"no 'Push to Main' run found for HEAD {local_head[:8]} — did the push trigger CI?")
    deadline = time.monotonic() + CI_WAIT_TIMEOUT_SEC
    announced = False
    while True:
        status, conclusion = _workflow_run_state(run_id)
        if status == "completed":
            if conclusion != "success":
                fail_with_message(f"'Push to Main' run for HEAD {local_head[:8]} concluded '{conclusion}'")
            return run_id
        if not announced:
            print(f"       CI for HEAD {local_head[:8]} is {status} — waiting up to {CI_WAIT_TIMEOUT_SEC // 60} min")
            announced = True
        if time.monotonic() >= deadline:
            fail_with_message(f"timed out after {CI_WAIT_TIMEOUT_SEC // 60} min waiting for CI on {local_head[:8]}")
        time.sleep(CI_POLL_INTERVAL_SEC)


def _fetch_release_metrics() -> dict[str, float]:
    """Download CI's cumulative metrics for the commit being released.

    The numbers come from the matrix combine job, not a local run, so the
    badge matches the CI gate exactly. It waits up to `CI_WAIT_TIMEOUT_SEC` for HEAD's
    'Push to Main' run to succeed, and exits when no such run succeeds in time.
    """
    local_head = run_command(["git", "rev-parse", "HEAD"]).strip()
    run_id = _wait_for_main_ci(local_head)
    with tempfile.TemporaryDirectory() as tmp:
        run_command(["gh", "run", "download", run_id, "--name", "release-metrics", "--dir", tmp])
        return json.loads((Path(tmp) / "metrics.json").read_text())


def step_9_gather_badge_metrics() -> BadgeMetrics:
    """Resolve every badge number, failing the release if any of them cannot be obtained."""
    print_step(9, "gather badge metrics (CI metrics for HEAD)")
    metrics = _fetch_release_metrics()
    union = int(metrics["test_union"])
    max_combo = int(metrics["test_max"])
    if max_combo and union > TEST_COUNT_UNION_RATIO_WARN * max_combo:
        print(
            f"\nWARNING: cumulative test count ({union}) exceeds "
            f"{TEST_COUNT_UNION_RATIO_WARN}x the largest single combo ({max_combo}). "
            "Node-id mismatches across combos can inflate the union — verify before publishing.\n",
            file=sys.stderr,
        )
    return BadgeMetrics(coverage_pct=float(metrics["coverage_pct"]), test_union=union)


# ==================================================================================================
#  release commit steps
# ==================================================================================================
def step_10_bump_version(version: str) -> None:
    """Set version in pyproject.toml."""
    print_step(10, f"bump version to {version}")
    run_command(["uv", "version", version])


def step_11_lock() -> None:
    """Refresh uv.lock after version bump."""
    print_step(11, "refresh uv.lock")
    run_command(["uv", "lock"])


def step_12_finalize_changelog(version: str) -> None:
    """Move Unreleased entries to a dated version section."""
    print_step(12, f"finalize CHANGELOG.md '## Unreleased' -> '## {version} ({date.today().isoformat()})'")
    text = CHANGELOG.read_text()
    m = re.search(r"^## Unreleased\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        fail_with_message("no '## Unreleased' section to finalize")
    body = m.group(1)
    new_body_lines: list[str] = []
    lines = body.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        cat_match = re.match(r"^### (\w+)\s*$", line)
        if cat_match and cat_match.group(1) in CATEGORIES:
            j = i + 1
            has_entry = False
            while j < len(lines) and not re.match(r"^### ", lines[j]):
                if lines[j].lstrip().startswith("- "):
                    has_entry = True
                    break
                j += 1
            if has_entry:
                new_body_lines.append(line)
                i += 1
                while i < len(lines) and not re.match(r"^### ", lines[i]):
                    new_body_lines.append(lines[i])
                    i += 1
            else:
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
        else:
            new_body_lines.append(line)
            i += 1
    tail = text[m.end() :]
    new_body = "".join(new_body_lines).rstrip() + ("\n\n" if tail else "\n")
    new_header = f"## {version} ({date.today().isoformat()})\n"
    text = text[: m.start()] + new_header + new_body + tail
    CHANGELOG.write_text(text)


def _coverage_color(pct: float) -> str:
    """Map a coverage percentage to a shields.io badge color."""
    if pct >= 90:
        return "brightgreen"
    return "yellow" if pct >= 75 else "red"


def refresh_readme_badges(badges: BadgeMetrics) -> None:
    """Stamp the README coverage + test-count badges from the metrics in `badges`."""
    text = README.read_text()
    text = COVERAGE_BADGE_RE.sub(
        f"badge/coverage-{badges.coverage_pct:.2f}%25-{_coverage_color(badges.coverage_pct)}",
        text,
    )
    text = TESTS_BADGE_RE.sub(f"badge/tests-{badges.test_union}-blue", text)
    README.write_text(text)


def stamp_splash(version: str) -> None:
    """Stamp the release version onto the committed splash webp (needs ImageMagick).

    Runs the second stage of ``create_splash.sh`` (the version overlay) on the
    committed, version-independent base image. `step_8_check_stamping_inputs` has
    already checked that ImageMagick and the script's inputs are present.
    """
    run_command(["sh", str(SPLASH_SCRIPT), f"v{version}"], cwd=REPO_ROOT)


def step_13_commit_release(version: str, badges: BadgeMetrics) -> None:
    """Refresh README badges, stamp the splash, then create the release commit."""
    print_step(13, f"refresh README badges + stamp splash + commit 'release: {version}'")
    refresh_readme_badges(badges)
    stamp_splash(version)
    run_command(["git", "add", "pyproject.toml", "uv.lock", "CHANGELOG.md", "README.md", str(SPLASH_WEBP)])
    run_command(["git", "commit", "-m", f"release: {version}"])


def step_14_tag(version: str) -> None:
    """Create the version tag."""
    print_step(14, f"create tag v{version}")
    run_command(["git", "tag", f"v{version}"])


# ==================================================================================================
#  post-release steps
# ==================================================================================================
def step_15_add_unreleased_section() -> None:
    """Add a fresh Unreleased section to the changelog."""
    print_step(15, "add fresh '## Unreleased' section to CHANGELOG.md")
    text = CHANGELOG.read_text()
    m = re.search(r"^## ", text, re.MULTILINE)
    if not m:
        fail_with_message("CHANGELOG.md has no version sections")
    insertion = "## Unreleased\n\n" + "\n".join(f"### {c}\n" for c in CATEGORIES) + "\n"
    text = text[: m.start()] + insertion + text[m.start() :]
    CHANGELOG.write_text(text)


def step_16_commit_next_cycle() -> None:
    """Commit the fresh Unreleased section."""
    print_step(16, "commit 'chore: begin next development cycle'")
    run_command(["git", "add", "CHANGELOG.md"])
    run_command(["git", "commit", "-m", "chore: begin next development cycle"])


def step_17_push(version: str) -> None:
    """Push main and the tag atomically."""
    print_step(17, f"push main + v{version} atomically")
    run_command(["git", "push", "--atomic", "origin", "main", f"refs/tags/v{version}"])


# ==================================================================================================
#  orchestration
# ==================================================================================================
def post_tag_recovery_hint(version: str, also_next_cycle: bool) -> None:
    """Print recovery instructions after a post-tag failure."""
    reset_count = 2 if also_next_cycle else 1
    print(
        f"\nERROR: a post-tag step failed.\n"
        f"Local state: release commit and tag v{version} created, not pushed.\n"
        f"To abort and retry:\n"
        f"  git tag -d v{version}\n"
        f"  git reset --hard HEAD~{reset_count}\n",
        file=sys.stderr,
    )


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="X.Y.Z (no leading v)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run every check, including the CI badge-metrics fetch, then stop before the first write",
    )
    args = parser.parse_args()
    version = args.version
    parse_semver(version)

    print(f"Releasing {PACKAGE_NAME} v{version}\n")

    print("Validation:")
    step_1_check_working_tree()
    step_2_check_in_sync()
    step_3_check_version_upgrade(version)
    step_4_check_tag_doesnt_exist(version)
    step_5_check_pypi_doesnt_have(version)
    step_6_check_classifiers_match()
    step_7_check_changelog_has_entries()
    step_8_check_stamping_inputs()
    badges = step_9_gather_badge_metrics()

    if args.dry_run:
        print(
            f"\nDry run: every check passed and nothing was written.\n"
            f"  coverage {badges.coverage_pct:.2f}% | tests {badges.test_union}\n"
        )
        return

    print("\nRelease commit:")
    step_10_bump_version(version)
    step_11_lock()
    step_12_finalize_changelog(version)
    step_13_commit_release(version, badges)
    step_14_tag(version)

    print("\nPost-release:")
    also_next_cycle = False
    try:
        step_15_add_unreleased_section()
        step_16_commit_next_cycle()
        also_next_cycle = True
        step_17_push(version)
    except subprocess.CalledProcessError:
        post_tag_recovery_hint(version, also_next_cycle)
        sys.exit(1)
    except SystemExit:
        post_tag_recovery_hint(version, also_next_cycle)
        raise


if __name__ == "__main__":
    main()
