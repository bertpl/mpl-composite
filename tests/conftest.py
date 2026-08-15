# Force matplotlib's headless Agg backend for the whole suite before any test imports pyplot,
# so renders stay deterministic and no interactive backend starts under pytest-xdist.
import matplotlib

matplotlib.use("Agg", force=True)
