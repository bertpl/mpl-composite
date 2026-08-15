import matplotlib.pyplot as plt
import pytest


@pytest.fixture
def fig_ax():
    fig, ax = plt.subplots()
    yield fig, ax
    plt.close(fig)
