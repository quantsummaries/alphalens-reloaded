"""Saving a report must not change the aggregation of its quantile returns."""

from unittest.mock import patch

from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import pytest
from PIL import Image

from alphalens import performance, plotting, utils, wrapper


@pytest.mark.parametrize("tables_as_figures", [False, True])
@pytest.mark.parametrize("long_short,group_neutral", [(False, False), (True, False), (True, True)])
def test_grouped_return_summary_is_identical_when_saved(
    tmp_path, tables_as_figures, long_short, group_neutral,
):
    dates = pd.bdate_range("2026-01-05", periods=8)
    index = pd.MultiIndex.from_product([dates, range(10)], names=["date", "asset"])
    # Each quantile has one member from the small group and four from the large
    # group. Their returns differ, so averaging group means gives a wrong result.
    data = pd.DataFrame(
        {
            "factor": np.tile(np.arange(1., 11.), len(dates)),
            "factor_quantile": np.tile([1] * 5 + [2] * 5, len(dates)),
            "group": np.tile(["small", "large", "large", "large", "large"] * 2, len(dates)),
            "1D": np.concatenate([
                scale * np.array([.1, 0, 0, 0, 0, .2, .02, .02, .02, .02])
                for scale in np.linspace(.9, 1.1, len(dates))
            ]),
        },
        index=index,
    )
    expected_mean, expected_error = performance.mean_return_by_quantile(
        data, by_group=True, demeaned=long_short, group_adjust=group_neutral,
    )
    original_data = data.copy(deep=True)
    tables = []
    original_plot = plotting.plot_returns_table

    def capture(*args, **kwargs):
        table = original_plot(*args, **kwargs)
        tables.append(table.copy())
        return table

    def fast_raster(figure, destination, **kwargs):
        # Keep the real export/figure-selection path without rasterizing the
        # large tear sheet; this test verifies calculations and save invariance.
        Image.new("RGB", (2, 2)).save(destination, format="PNG")

    destination = tmp_path / "grouped.png"
    with (
        patch.object(plotting, "plot_returns_table", side_effect=capture),
        patch.object(Figure, "savefig", fast_raster),
        patch.object(utils, "print_table"),
        patch.object(utils, "display"),
    ):
        unsaved = wrapper.return_analysis_wrapper(
            data, long_short=long_short, group_neutral=group_neutral,
            by_group=True, tables_as_figures=tables_as_figures,
        )
        saved = wrapper.return_analysis_wrapper(
            data, long_short=long_short, group_neutral=group_neutral,
            by_group=True, tables_as_figures=tables_as_figures,
            tear_sheet_filepath=str(destination),
        )

    assert destination.is_file()
    assert len(tables) == 2
    pd.testing.assert_frame_equal(tables[0], tables[1])
    for result, table in zip([unsaved, saved], tables, strict=True):
        pd.testing.assert_frame_equal(result["return_summary"], table)
        pd.testing.assert_frame_equal(result["mean_return_by_q"], expected_mean)
        pd.testing.assert_frame_equal(result["std_err_by_q"], expected_error)
        assert result["mean_return_by_q"].index.names == ["factor_quantile", "group"]
    pd.testing.assert_frame_equal(data, original_data)
    # The pooled spread is 50% * (5.6% - 2.0%) = 1.8%, rather than the
    # 3.0% obtained by giving the two unequal groups equal weight.
    assert tables[0].loc["Mean Period Wise Spread (bps, 100% gross)", "1D"] == pytest.approx(180)
    if not long_short and not group_neutral:
        assert tables[0].loc["Mean Period Wise Return Top Quantile (bps)", "1D"] == pytest.approx(560)
        assert tables[0].loc["Mean Period Wise Return Bottom Quantile (bps)", "1D"] == pytest.approx(200)
