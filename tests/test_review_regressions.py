"""Regression coverage for horizon, calendar, event and grouped-IC contracts."""

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from pandas.testing import assert_frame_equal, assert_series_equal
from pandas.tseries.offsets import BDay, CustomBusinessDay

from alphalens import performance as perf, plotting, tears, utils, wrapper


def panel(dates, assets=("A", "B")):
    index = pd.MultiIndex.from_product([dates, assets], names=["date", "asset"])
    return pd.DataFrame(
        {"factor": np.tile(np.arange(1, len(assets) + 1), len(dates)),
         "factor_quantile": np.tile(np.arange(1, len(assets) + 1), len(dates))},
        index=index,
    )


def test_alpha_beta_preserves_series_horizon_and_input():
    dates = pd.bdate_range("2026-01-05", periods=20)
    data = panel(dates)
    rng = np.random.default_rng(42)
    data["1D"] = np.repeat(rng.normal(0, .01, len(dates)), 2)
    market = rng.normal(0, .02, len(dates))
    data["5D"] = np.repeat(market, 2)
    returns = pd.Series(.001 + .4 * market, index=dates, name="5D")
    original = returns.copy()
    actual = perf.factor_alpha_beta(data, returns)
    assert_frame_equal(actual, perf.factor_alpha_beta(data, returns.to_frame()))
    assert actual.loc["beta", "5D"] == pytest.approx(.4)
    assert_series_equal(returns, original)
    with pytest.raises(ValueError, match="unnamed"):
        perf.factor_alpha_beta(data, returns.rename(None))
    with pytest.raises(ValueError, match="Unknown return horizon"):
        perf.factor_alpha_beta(data, returns.rename("10D"))
    single = data.drop(columns="1D")
    assert_frame_equal(actual, perf.factor_alpha_beta(single, returns.rename(None)))


@pytest.mark.parametrize("freq", [BDay(2), CustomBusinessDay(2, holidays=["2026-01-06"])])
def test_sample_frequency_does_not_multiply_holding_period(freq):
    start = pd.Timestamp("2026-01-05")
    expected = start + freq.base * 2
    assert utils.add_custom_calendar_timedelta(start, pd.Timedelta("2D"), freq) == expected
    data = panel(pd.date_range(start, periods=2, freq=freq))
    data["2D"] = .01
    positions = perf.factor_positions(data, "2D")
    assert_allclose(positions.loc[expected], [-.5, .5])
    assert positions.index[-1] == data.index.levels[0][-1] + freq.base * 2


def test_cleaned_intraday_data_supports_positions_and_pyfolio():
    dates = pd.date_range("2026-01-05 09:30", periods=6, freq="h")
    prices = pd.DataFrame({"A": np.arange(100., 106.), "B": np.arange(100., 112., 2)}, index=dates)
    factor = panel(dates[:4])["factor"]
    clean = utils.get_clean_factor_and_forward_returns(factor, prices, periods=(1,), quantiles=2)
    positions = perf.factor_positions(clean, "1h")
    assert positions.index[-1] == dates[4]
    assert_allclose(positions.iloc[-1], 0)
    returns, positions, _ = perf.create_pyfolio_input(clean, "1h", capital=100)
    assert returns.notna().all()
    assert positions.notna().all().all()
    assert_allclose(positions.iloc[-1, :-1], 0)
    assert positions.iloc[-1]["cash"] == pytest.approx(100 * (1 + returns).prod())


def test_pyfolio_preserves_first_return_and_terminal_capital():
    data = panel(pd.bdate_range("2026-01-05", periods=3))
    data["1D"] = np.repeat([.1, .2, .3], 2)
    returns, positions, benchmark = perf.create_pyfolio_input(data, "1D", long_short=False, capital=100)
    assert_allclose(returns, [.1, .2, .3])
    assert_allclose(benchmark, returns)
    terminal_value = 100 * 1.1 * 1.2 * 1.3
    assert_allclose(positions.sum(axis=1), [110, 132, terminal_value, terminal_value])
    assert_allclose(positions.iloc[-1], [0, 0, terminal_value])


@pytest.mark.parametrize("frequency", [None, "B"])
def test_quantile_reentry_after_empty_observed_date(frequency):
    dates = pd.date_range("2026-01-05", periods=3, freq="B")
    if frequency is None:
        dates = pd.DatetimeIndex(dates.to_numpy())
    data = panel(dates)
    q = pd.Series([1, 2, 2, 2, 1, 2], index=data.index)
    actual = perf.quantile_turnover(q, 1)
    assert np.isnan(actual.iloc[0])
    assert np.isnan(actual.iloc[1])
    assert actual.iloc[2] == 1
    assert perf.quantile_turnover(q, 9).isna().all()


def test_missing_observed_date_is_not_an_empty_quantile():
    dates = pd.bdate_range("2026-01-05", periods=3)
    data = panel(dates)
    q = data["factor_quantile"].drop(index=dates[1], level="date")
    turnover = perf.quantile_turnover(q, 1)
    assert turnover.isna().all()


def test_pyfolio_carries_held_positions_over_weekend():
    data = panel(pd.bdate_range("2026-01-09", periods=2))
    data["2D"] = .01
    _, positions, _ = perf.create_pyfolio_input(data, "2D", long_short=False)
    assert_allclose(positions.loc["2026-01-10", ["A", "B"]], [1/3, 2/3])
    assert_allclose(positions.iloc[-1], [0, 0, 1])


@pytest.mark.parametrize("cumulative", [False, True])
@pytest.mark.parametrize("mean_by_date", [False, True])
@pytest.mark.parametrize("demeaned", [False, True])
@pytest.mark.parametrize("before,after", [(0, 2), (2, 0), (6, 6)])
def test_event_windows_are_rebased_before_aggregation(cumulative, mean_by_date, demeaned, before, after):
    dates = pd.bdate_range("2026-01-05", periods=9)
    rates = np.array([.01, -.02])
    daily = pd.DataFrame(np.tile(rates, (9, 1)), index=dates, columns=["A", "B"])
    wealth = (1 + daily).cumprod() * [7, 200]
    events = panel(dates[[2, 5]])["factor"]
    result = perf.common_start_returns(
        events, wealth if cumulative else daily, before, after,
        cumulative=cumulative, mean_by_date=mean_by_date,
        demean_by=events if demeaned else None,
    )
    # Constant returns imply identical event-relative paths despite different
    # histories/initial wealth; the outer windows are truncated at data edges.
    expected_windows = []
    for event_row in [2, 5]:
        offsets = np.arange(max(-before, -event_row), min(after, 8-event_row) + 1)
        values = (1 + rates) ** offsets[:, None] - 1
        if demeaned:
            values -= values.mean(axis=1, keepdims=True)
        expected_windows.append(pd.DataFrame(values, index=offsets, columns=["A", "B"]))
    if mean_by_date:
        expected_windows = [window.mean(axis=1) for window in expected_windows]
    expected = pd.concat(expected_windows, axis=1)
    assert_allclose(result, expected, atol=1e-14, equal_nan=True)
    assert_allclose(result.loc[0], 0, atol=1e-14)


@pytest.mark.parametrize("cumulative", [False, True])
@pytest.mark.parametrize("group_adjust", [False, True])
@pytest.mark.parametrize("by_group", [False, True])
def test_event_quantiles_accept_daily_returns_and_explicit_wealth(cumulative, group_adjust, by_group):
    dates = pd.bdate_range("2026-01-05", periods=7)
    daily = pd.DataFrame({"A": .01, "B": .02, "C": -.01, "D": -.02}, index=dates)
    events = panel(dates[[2, 4]], tuple(daily.columns))
    events["factor_quantile"] = [1, 2, 1, 2] * 2
    events["group"] = ["X", "X", "Y", "Y"] * 2
    result = perf.average_cumulative_return_by_quantile(
        events, (1 + daily).cumprod() if cumulative else daily,
        periods_before=0, periods_after=2, demeaned=False,
        group_adjust=group_adjust, by_group=by_group, cumulative=cumulative,
    )
    paths = (1 + daily.iloc[0].to_numpy()) ** np.arange(3)[:, None] - 1
    if group_adjust:
        paths[:, :2] -= paths[:, :2].mean(axis=1, keepdims=True)
        paths[:, 2:] -= paths[:, 2:].mean(axis=1, keepdims=True)
    if by_group:
        for group, start in [("X", 0), ("Y", 2)]:
            for q in [1, 2]:
                assert_allclose(result.loc[(q, "mean", group)], paths[:, start+q-1], atol=1e-14)
    else:
        for q in [1, 2]:
            assert_allclose(result.loc[(q, "mean")], paths[:, [q-1, q+1]].mean(axis=1), atol=1e-14)


def test_event_averages_give_dates_equal_weight_with_changing_universe():
    dates = pd.bdate_range("2026-01-05", periods=7)
    daily = pd.DataFrame({"A": .01, "B": .03, "C": .03, "D": .03}, index=dates)
    index = pd.MultiIndex.from_tuples(
        [(dates[2], "A"), *[(dates[4], asset) for asset in "BCD"]],
        names=["date", "asset"],
    )
    events = pd.DataFrame({"factor": 1., "factor_quantile": 1}, index=index)
    result = perf.average_cumulative_return_by_quantile(
        events, daily, periods_before=0, periods_after=2, demeaned=False,
    )
    assert_allclose(result.loc[(1, "mean")], [0, .02, .0405], atol=1e-14)
    assert_allclose(result.loc[(1, "std")], [0, .02 / np.sqrt(2), .0408 / np.sqrt(2)], atol=1e-14)


def information_panel():
    dates = pd.bdate_range("2026-01-05", periods=12)
    data = panel(dates, tuple("ABCDEFGH"))
    rng = np.random.default_rng(42)
    data["factor"] = rng.normal(size=len(data))
    data["1D"] = rng.normal(0, .01, len(data))
    data["group"] = np.tile(["X"]*4 + ["Y"]*4, len(dates))
    return data


def test_group_diagnostics_match_independent_group_calculations():
    data = information_panel()
    ic = perf.factor_information_coefficient(data, by_group=True)
    actual = plotting.plot_information_table(ic, return_df=True, lag=1)
    assert actual.index.names == ["group", "horizon"]
    for group in ["X", "Y"]:
        expected = plotting.plot_information_table(ic.xs(group, level="group"), return_df=True, lag=1)
        assert_frame_equal(actual.xs(group, level="group"), expected, check_names=False)
    renamed = data.assign(group=data["group"].map({"X": "Y", "Y": "X"}))
    other = plotting.plot_information_table(perf.factor_information_coefficient(renamed, by_group=True), return_df=True, lag=1)
    assert_allclose(actual.loc["X"], other.loc["Y"], equal_nan=True)


@pytest.mark.parametrize("saved", [False, True])
def test_undefined_ic_horizon_does_not_remove_valid_horizon(saved, tmp_path):
    data = information_panel()
    data["5D"] = .01
    expected = perf.factor_information_coefficient(data)["1D"].mean()
    result = wrapper.information_analysis_wrapper(
        data, tables_as_figures=False,
        tear_sheet_filepath=str(tmp_path / "ic.pdf") if saved else None,
    )
    assert result["ic_spearman"].loc["IC Mean (spearman)", "1D"] == pytest.approx(expected)
    assert result["ic_spearman"]["5D"].isna().all()


def test_summary_forwards_group_neutrality_to_ic():
    data = information_panel()
    expected = perf.factor_information_coefficient(data, group_adjust=True)
    seen = []
    with patch.object(plotting, "plot_information_table", side_effect=lambda ic, **kw: seen.append(ic)), patch.object(tears, "_maybe_show"):
        tears.create_summary_tear_sheet(data, group_neutral=True, tables_as_figures=False)
    assert_frame_equal(seen[0], expected)


def test_ic_time_series_accepts_single_axis_and_rejects_too_few():
    ic = perf.factor_information_coefficient(information_panel())
    _, axis = plt.subplots()
    result = plotting.plot_ic_ts(ic, ax=axis)
    assert result[0] is axis
    assert_allclose(axis.lines[0].get_ydata(), ic["1D"])
    with pytest.raises(ValueError, match="at least 2 axes"):
        plotting.plot_ic_ts(ic.assign(**{"5D": ic["1D"]}), ax=axis)


def intraday_panel():
    data = panel(pd.date_range("2026-01-05 09:30", periods=8, freq="h"), tuple("ABCD"))
    data["factor"] = np.tile([1., 2., 3., 4., 4., 3., 2., 1.], 4)
    data["factor_quantile"] = np.tile([1, 1, 2, 2, 2, 2, 1, 1], 4)
    data["1h"] = np.random.default_rng(42).normal(0, .001, len(data))
    return data


@pytest.mark.parametrize("generator", [tears.create_summary_tear_sheet, tears.create_turnover_tear_sheet, tears.create_full_tear_sheet])
@pytest.mark.parametrize("lags", [None, [1, 2]])
def test_intraday_tear_sheets_use_observation_lags(generator, lags):
    data = intraday_panel()
    displayed = []
    original = plotting.plot_turnover_table

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        displayed.append(result)
        return result

    with patch.object(plotting, "plot_turnover_table", side_effect=capture), patch.object(tears, "_maybe_show"), patch.object(utils, "print_table"):
        generator(data, turnover_lags=lags, tables_as_figures=False)
    assert len(displayed) == 1
    turnover, autocorr = displayed[0]
    expected_lags = [1] if lags is None else lags
    assert turnover.columns.tolist() == [plotting._observation_label(p) for p in expected_lags]
    assert turnover.loc["Quantile 1 Mean Turnover ", "1 observation"] == 1
    for lag in expected_lags:
        label = plotting._observation_label(lag)
        expected = perf.factor_rank_autocorrelation(data, lag).mean()
        assert autocorr.loc["Mean Factor Rank Autocorrelation", label] == pytest.approx(expected)
        for quantile in [1, 2]:
            expected = perf.quantile_turnover(data["factor_quantile"], quantile, lag).mean()
            assert turnover.loc[f"Quantile {quantile} Mean Turnover ", label] == expected


@pytest.mark.parametrize("generator", [tears.create_summary_tear_sheet, tears.create_turnover_tear_sheet, tears.create_full_tear_sheet])
@pytest.mark.parametrize("lags", [[], [0], [-1], [1.5], [True], ["1"], [None], 1])
def test_invalid_turnover_lags_fail_before_allocating_figures(generator, lags):
    before = set(plt.get_fignums())
    with pytest.raises(ValueError, match="non-empty sequence of positive integers"):
        generator(intraday_panel(), turnover_lags=lags)
    assert set(plt.get_fignums()) == before


@pytest.mark.parametrize("periods", [[], ["0D"], ["-1D"], ["30m"], ["1D1h"], ["NaT"], ["invalid"]])
def test_invalid_legacy_turnover_periods_are_not_truncated(periods):
    before = set(plt.get_fignums())
    with pytest.raises(ValueError, match="positive whole-day durations"):
        tears.create_turnover_tear_sheet(intraday_panel(), turnover_periods=periods)
    assert set(plt.get_fignums()) == before


def test_turnover_lag_defaults_preserve_daily_behavior_and_remove_duplicates():
    data = intraday_panel().assign(**{"5D": .01, "1D": .01, "0D": 0., "1D1h": .01})
    assert tears._resolve_turnover_lags(data) == [5, 1]
    assert tears._resolve_turnover_lags(data, turnover_periods=["2D", "1D", "2D"]) == [2, 1]
    assert tears._resolve_turnover_lags(data, turnover_lags=[np.int64(2), 1, 2]) == [2, 1]
    with pytest.raises(ValueError, match="only one"):
        tears.create_turnover_tear_sheet(data, turnover_lags=[1], turnover_periods=["1D"])


@pytest.mark.parametrize("function", [plotting.plot_ic_hist, plotting.plot_ic_qq])
def test_ic_distribution_plots_accept_single_axes_and_arrays(function):
    ic = perf.factor_information_coefficient(information_panel())
    _, axis = plt.subplots()
    assert function(ic, ax=axis)[0] is axis
    assert axis.has_data()
    two_horizons = ic.assign(**{"5D": ic["1D"] / 2})
    _, axes = plt.subplots(1, 2)
    result = function(two_horizons, ax=axes.reshape(1, 2))
    assert result.tolist() == axes.tolist()
    assert all(axis.has_data() for axis in axes)
    with pytest.raises(ValueError, match="at least 2 axes"):
        function(two_horizons, ax=axis)
