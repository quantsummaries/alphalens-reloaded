"""Event distributions must handle a zero-length date range."""

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from alphalens import plotting, tears


@pytest.mark.parametrize("supplied_axis", [False, True])
@pytest.mark.parametrize("timezone", [None, "UTC", "Australia/Sydney"])
@pytest.mark.parametrize("asset_count", [1, 4])
def test_single_event_date_renders_one_count_bar(supplied_axis, timezone, asset_count):
    date = pd.Timestamp("2026-01-05 09:00", tz=timezone)
    index = pd.MultiIndex.from_product([[date], range(asset_count)], names=["date", "asset"])
    events = pd.Series(np.arange(asset_count, dtype=float), index=index)
    axis = plt.subplots()[1] if supplied_axis else None
    result = plotting.plot_events_distribution(events, ax=axis)
    if supplied_axis:
        assert result is axis
    assert len(result.patches) == 1
    assert result.patches[0].get_height() == asset_count
    assert len(result.get_xticklabels()) == 1
    assert "2026-01-05" in result.get_xticklabels()[0].get_text()
    assert result.get_title() == "Distribution of events in time"
    assert result.get_ylabel() == "Number of events"


def test_single_date_excludes_missing_values_from_the_count():
    index = pd.MultiIndex.from_product(
        [[pd.Timestamp("2026-01-05")], range(3)], names=["date", "asset"]
    )
    axis = plotting.plot_events_distribution(pd.Series([0., np.nan, 1.], index=index))
    assert len(axis.patches) == 1
    assert axis.patches[0].get_height() == 2


def test_multiple_event_dates_still_use_time_bins():
    dates = pd.date_range("2026-01-05", periods=3)
    index = pd.MultiIndex.from_product([dates, ["A", "B"]], names=["date", "asset"])
    axis = plotting.plot_events_distribution(pd.Series(1., index=index), num_bars=2)
    assert len(axis.patches) > 1
    assert sum(bar.get_height() for bar in axis.patches) == len(index)


def test_event_study_tear_sheet_supports_a_single_event_date():
    event_date = pd.Timestamp("2026-01-07")
    index = pd.MultiIndex.from_product([[event_date], list("ABCD")], names=["date", "asset"])
    data = pd.DataFrame(
        {"factor": [1., 2., 3., 4.], "factor_quantile": [1, 1, 2, 2],
         "1D": [.01, .02, -.01, -.02]}, index=index,
    )
    daily = pd.DataFrame(
        {"A": .01, "B": .02, "C": -.01, "D": -.02},
        index=pd.bdate_range("2026-01-05", periods=5),
    )
    axes = []
    original = plotting.plot_events_distribution

    def capture(*args, **kwargs):
        axis = original(*args, **kwargs)
        axes.append(axis)
        return axis

    with (
        patch.object(plotting, "plot_events_distribution", side_effect=capture),
        patch.object(tears, "_maybe_show"),
        patch.object(plotting.utils, "print_table"),
    ):
        tears.create_event_study_tear_sheet(data, daily, avgretplot=(1, 1))
    assert len(axes) == 1
    assert len(axes[0].patches) == 1
    assert axes[0].patches[0].get_height() == 4
