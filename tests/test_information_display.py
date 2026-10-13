"""Regression coverage for information wrapper display options."""

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from alphalens.wrapper import information_analysis_wrapper


@pytest.mark.parametrize("return_df", [False, True])
@pytest.mark.parametrize("as_figure", [False, True])
def test_information_wrapper_returns_data_with_independent_display(return_df, as_figure):
    index = pd.MultiIndex.from_product(
        [pd.date_range("2024-01-01", periods=20), list("ABCDEF")],
        names=["date", "asset"],
    )
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {"factor": rng.normal(size=len(index)), "1D": rng.normal(size=len(index))},
        index=index,
    )
    existing_figures = set(plt.get_fignums())
    try:
        with patch("alphalens.plotting.utils.print_table") as display:
            result = information_analysis_wrapper(
                data, return_df=return_df, as_figure=as_figure
            )
        assert display.call_count == (0 if return_df else 2)
        assert set(result) == {"ic_spearman", "ic_pearson"}
        for ic_type in ["spearman", "pearson"]:
            summary = result[f"ic_{ic_type}"]
            assert isinstance(summary, pd.DataFrame)
            assert list(summary.columns) == ["1D"]
            assert f"IC Mean ({ic_type})" in summary.index
        figures = set(plt.get_fignums()) - existing_figures
        assert len(figures) == (2 if as_figure else 0)
        for number in figures:
            assert len(plt.figure(number).axes[0].tables) == 1
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)
