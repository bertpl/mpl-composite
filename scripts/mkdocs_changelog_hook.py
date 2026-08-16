"""mkdocs build hook: publish the repo-root CHANGELOG.md as the changelog page.

Wired via `hooks:` in mkdocs.yml. A plain hook needs no third-party include plugin, and generating
the page keeps CHANGELOG.md from being duplicated under docs/.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.structure.files import File

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Add the repo-root CHANGELOG.md to the site as the generated changelog page."""
    changelog = Path(config.config_file_path).parent / "CHANGELOG.md"
    files.append(File.generated(config, "changelog.md", content=changelog.read_text()))
    return files
