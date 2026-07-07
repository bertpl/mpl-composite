import matplotlib.pyplot as plt
import pytest

from mpl_composite import save_figure


@pytest.fixture
def fig():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    yield fig
    plt.close(fig)


def test_save_figure_writes_each_format(tmp_path, fig) -> None:
    # --- act --------------------------
    written = save_figure(fig, tmp_path / "out.png", formats=("png", "pdf"))

    # --- assert -----------------------
    assert [p.suffix for p in written] == [".png", ".pdf"]
    assert all(p.exists() and p.stat().st_size > 0 for p in written)


def test_save_figure_accepts_string_paths(tmp_path, fig) -> None:
    # --- act --------------------------
    written = save_figure(fig, str(tmp_path / "out"), formats=("png",))

    # --- assert -----------------------
    assert written[0].name == "out.png"
    assert written[0].exists()
