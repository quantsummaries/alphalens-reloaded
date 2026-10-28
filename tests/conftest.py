import matplotlib
import matplotlib.pyplot as plt
import pytest

# Force a non-interactive backend for deterministic, headless test runs.
matplotlib.use("Agg", force=True)


@pytest.fixture(autouse=True)
def _close_matplotlib_figures():
	yield
	plt.close("all")


