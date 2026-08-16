"""mkdocs build hook: generate the example gallery from the figure registry.

Render each gallery figure to a PNG at build time and emit a gallery page pairing the image with
its construction code, so the published gallery always matches the figures the code produces.

The figures live in the test suite's gallery module, which carries no test-framework dependencies;
this hook loads it by path rather than duplicating the figure code.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import io
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
from mkdocs.structure.files import File

matplotlib.use("Agg", force=True)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

    from mpl_composite import CompositeFigure

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GALLERY_PATH = _REPO_ROOT / "tests" / "visual" / "gallery.py"
_GALLERY_DPI = 150

# One-line captions live here, not in the figures' own docstrings: those describe what each figure
# pins for the regression suite, in test-oriented terms unfit for the public gallery.
_CAPTIONS = {
    "demo_composite": "A title over a nested 2x2 grid of text and spacers.",
    "plot_axes_demo": "An x/y plot: linear x, log y, curves, samples, an annotation, a legend.",
    "linlog_plot_demo": "A plot with an automatic lin-log y axis: linear below 1, log above.",
    "table_demo": "A banded table with grouped columns, titles, and per-cell text.",
    "plotting_table_demo": "A table whose last column is an embedded log-scale plot, with skewed labels.",
}


def _load_gallery() -> ModuleType:
    """Load the gallery module by path."""
    spec = importlib.util.spec_from_file_location("mpl_composite_gallery", _GALLERY_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the gallery module at {_GALLERY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # so inspect.getsource can resolve the classes' source file
    spec.loader.exec_module(module)
    return module


def _render_png(figure: CompositeFigure) -> bytes:
    """Render a composite figure to PNG bytes via an in-memory Agg savefig."""
    fig = figure.render()
    try:
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=_GALLERY_DPI, bbox_inches="tight")
        return buffer.getvalue()
    finally:
        plt.close(fig)


def _strip_docstrings(source: str) -> str:
    """Drop docstring lines from a source block, keeping its formatting and comments."""
    tree = ast.parse(source)
    drop: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        first = node.body[0] if node.body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            drop.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return "\n".join(line for i, line in enumerate(source.splitlines(), start=1) if i not in drop)


def _construction_code(builder: Callable[[], CompositeFigure], module: ModuleType) -> str:
    """Return the source shown for a figure: the gallery-defined classes it uses, then the builder."""
    sources = []
    for name in builder.__code__.co_names:
        obj = getattr(module, name, None)
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            sources.append(_strip_docstrings(inspect.getsource(obj)).rstrip())
    sources.append(_strip_docstrings(inspect.getsource(builder)).rstrip())
    return "\n\n\n".join(sources)


def _gallery_page(module: ModuleType) -> str:
    """Assemble the gallery markdown: one section per figure with its image and code."""
    lines = ["# Gallery", "", "Each figure is rendered from the code shown with it.", ""]
    for name, builder in module.GALLERY.items():
        title = name.replace("_", " ").capitalize()
        lines += [f"## {title}", ""]
        if name in _CAPTIONS:
            lines += [_CAPTIONS[name], ""]
        lines += [f"![{title}](images/{name}.png)", ""]
        lines += ["```python", _construction_code(builder, module), "```", ""]
    return "\n".join(lines)


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Inject the rendered gallery page and its figure images as generated files."""
    module = _load_gallery()
    for name, builder in module.GALLERY.items():
        files.append(File.generated(config, f"gallery/images/{name}.png", content=_render_png(builder())))
    files.append(File.generated(config, "gallery/index.md", content=_gallery_page(module)))
    return files
