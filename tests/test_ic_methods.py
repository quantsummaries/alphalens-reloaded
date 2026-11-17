"""Keep IC chart labels and aggregates consistent with their correlation method."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from alphalens import performance as perf, plotting, tears


@pytest.fixture
def nonlinear_panel():
    dates = pd.bdate_range("2024-01-02", periods=30, freq="2B")
    index = pd.MultiIndex.from_product([dates, range(10)], names=["date", "asset"])
    factor = np.tile(np.arange(10.), len(dates))
    return pd.DataFrame({
        "factor": factor, "1D5h50m": factor ** 3 / 100000,
        "group": np.tile(["A"] * 5 + ["B"] * 5, len(dates)),
    }, index=index)


@pytest.mark.parametrize("by_group", [False, True])
def test_information_charts_and_aggregates_use_each_method(nonlinear_panel, monkeypatch, by_group):
    data = nonlinear_panel
    calls = {name: [] for name in [
        "plot_ic_ts", "plot_ic_hist", "plot_ic_qq",
        "plot_monthly_ic_heatmap", "plot_ic_by_group",
    ]}
    for name in calls:
        def capture(values, *, ic_type, ax, name=name):
            calls[name].append((ic_type, values.copy()))
        monkeypatch.setattr(plotting, name, capture)
    original_table = plotting.plot_information_table
    monkeypatch.setattr(plotting, "plot_information_table", lambda ic, **kw: original_table(
        ic, return_df=True, ic_type=kw["ic_type"], lag=kw["lag"],
    ))
    monkeypatch.setattr(tears, "_maybe_show", lambda: None)
    before = set(plt.get_fignums())
    summaries = tears.create_information_tear_sheet(data, by_group=by_group)
    assert set(plt.get_fignums()) == before
    assert set(summaries) == {"spearman", "pearson"}
    for name in ["plot_ic_ts", "plot_ic_hist", "plot_ic_qq"]:
        assert [method for method, _ in calls[name]] == ["spearman", "pearson"]
        for method, actual in calls[name]:
            expected = perf.factor_information_coefficient(data, ic_type=method)
            assert_frame_equal(actual, expected)
    assert not calls["plot_ic_ts"][0][1].equals(calls["plot_ic_ts"][1][1])
    aggregate_name = "plot_ic_by_group" if by_group else "plot_monthly_ic_heatmap"
    unused_name = "plot_monthly_ic_heatmap" if by_group else "plot_ic_by_group"
    assert calls[unused_name] == []
    assert [method for method, _ in calls[aggregate_name]] == ["spearman", "pearson"]
    for method, actual in calls[aggregate_name]:
        daily = perf.factor_information_coefficient(data, by_group=by_group, ic_type=method)
        expected = daily.groupby(level="group").mean() if by_group else daily.resample("ME").mean()
        assert_frame_equal(actual, expected, check_freq=False)
        summary = original_table(daily, return_df=True, ic_type=method)
        assert_frame_equal(summaries[method], summary)


@pytest.mark.parametrize("method", ["spearman", "pearson"])
@pytest.mark.parametrize("name", [
    "plot_ic_ts", "plot_ic_hist", "plot_ic_qq",
    "plot_monthly_ic_heatmap", "plot_ic_by_group",
])
def test_chart_titles_identify_method(nonlinear_panel, name, method):
    data = nonlinear_panel
    values = perf.factor_information_coefficient(data, ic_type=method)
    if name == "plot_monthly_ic_heatmap":
        values = values.resample("ME").mean()
    elif name == "plot_ic_by_group":
        values = perf.mean_information_coefficient(data, by_group=True, ic_type=method)
    fig, axis = plt.subplots()
    try:
        getattr(plotting, name)(values, ax=[axis] if name == "plot_monthly_ic_heatmap" else axis, ic_type=method)
        assert method.title() in axis.get_title()
    finally:
        plt.close(fig)


@pytest.mark.parametrize("name", ["plot_ic_ts", "plot_ic_hist", "plot_ic_qq"])
def test_empty_ic_chart_identifies_method(name):
    values = pd.DataFrame({"1D": [np.nan]}, index=pd.date_range("2024-01-02", periods=1))
    fig, axis = plt.subplots()
    try:
        getattr(plotting, name)(values, ax=axis, ic_type="pearson")
        assert "Pearson" in axis.get_title()
    finally:
        plt.close(fig)


def test_mean_ic_rejects_unknown_method(nonlinear_panel):
    with pytest.raises(ValueError, match="Invalid information coefficient type"):
        perf.mean_information_coefficient(nonlinear_panel, ic_type="unknown")
