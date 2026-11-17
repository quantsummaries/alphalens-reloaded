"""Trading calendars use local dates; unavailable regressions remain undefined."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose
from pandas.tseries.offsets import BDay, CustomBusinessDay

from alphalens import performance, utils


@pytest.mark.parametrize(
    "timezone", [None, "UTC", "America/New_York", "Australia/Sydney", "Pacific/Auckland"]
)
@pytest.mark.parametrize(
    "start,calendar",
    [
        ("2026-01-05 09:00", BDay()),
        ("2026-01-09 09:00", BDay()),
        ("2026-01-05 09:00", CustomBusinessDay(holidays=["2026-01-06"])),
    ],
)
def test_forward_horizon_counts_local_trading_dates(timezone, start, calendar):
    dates = pd.date_range(start, periods=2, freq=calendar, tz=timezone)
    naive = utils.make_naive_ts(dates[0])
    assert naive.tzinfo is None
    assert naive == pd.Timestamp(start)
    assert utils.diff_custom_calendar_timedeltas(dates[0], dates[1], calendar) == pd.Timedelta("1D")
    # Exercise the public forward-return calculation with a single factor date:
    # a wrong calendar count cannot be hidden by the modal horizon calculation.
    index = pd.MultiIndex.from_product([dates[:1], ["A", "B"]], names=["date", "asset"])
    factor = pd.Series([1., 2.], index=index)
    prices = pd.DataFrame({"A": [100., 110.], "B": [100., 90.]}, index=dates)
    forward = utils.compute_forward_returns(factor, prices, periods=(1,))
    assert forward.columns.tolist() == ["1D"]
    assert_allclose(forward["1D"], [.1, -.1])


@pytest.mark.parametrize(
    "timezone,start",
    [("America/New_York", "2026-03-06 09:00"), ("Australia/Sydney", "2026-04-03 09:00")],
)
def test_trading_day_horizon_across_daylight_saving_weekend(timezone, start):
    test_forward_horizon_counts_local_trading_dates(timezone, start, BDay())


@pytest.mark.parametrize(
    "timezone,start",
    [("America/New_York", "2026-03-06 09:00"), ("Australia/Sydney", "2026-04-03 09:00")],
)
def test_pytz_and_zoneinfo_agree_on_trading_day_durations(timezone, start):
    pytz = pytest.importorskip("pytz")
    test_forward_horizon_counts_local_trading_dates(pytz.timezone(timezone), start, BDay())


def test_intraday_calendar_difference_preserves_elapsed_time_across_dst():
    start = pd.Timestamp("2026-03-08 01:30", tz="America/New_York")
    end = pd.Timestamp("2026-03-08 03:30", tz="America/New_York")
    assert utils.diff_custom_calendar_timedeltas(start, end, pd.offsets.Hour()) == pd.Timedelta("1h")


def regression_data():
    dates = pd.bdate_range("2026-01-05", periods=8)
    market = np.linspace(-.03, .03, len(dates))
    index = pd.MultiIndex.from_product([dates, ["A", "B"]], names=["date", "asset"])
    data = pd.DataFrame({"1D": np.repeat(market, 2), "5D": np.repeat(market, 2)}, index=index)
    returns = pd.DataFrame({"1D": .001 + .4 * market, "5D": .001 + .4 * market}, index=dates)
    return data, returns


@pytest.mark.parametrize("missing_side", ["portfolio", "universe"])
@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_unavailable_horizon_does_not_prevent_other_horizons_fitting(missing_side, invalid):
    data, returns = regression_data()
    if missing_side == "portfolio":
        returns["1D"] = invalid
    else:
        data["1D"] = invalid
    original_data, original_returns = data.copy(), returns.copy()
    result = performance.factor_alpha_beta(data, returns, periods_per_year=252)
    assert result.index.tolist() == ["Ann. alpha", "t-stat(alpha)", "beta", "t-stat(beta)"]
    assert result["1D"].isna().all()
    assert result.loc["beta", "5D"] == pytest.approx(.4)
    assert result.loc["Ann. alpha", "5D"] == pytest.approx(1.001**252 - 1)
    pd.testing.assert_frame_equal(data, original_data)
    pd.testing.assert_frame_equal(returns, original_returns)


@pytest.mark.parametrize("no_overlap", [False, True])
def test_regression_with_no_matched_observations_returns_nan(no_overlap):
    data, returns = regression_data()
    if no_overlap:
        returns.index = returns.index + pd.DateOffset(years=1)
    else:
        returns = returns.iloc[:0]
    result = performance.factor_alpha_beta(data, returns)
    assert result.shape == (4, 2)
    assert result.isna().all().all()


def test_regression_drops_nonfinite_pairs_before_fitting():
    data, returns = regression_data()
    data.loc[(returns.index[0], slice(None)), "1D"] = np.inf
    returns.loc[returns.index[1], "1D"] = np.nan
    returns.loc[returns.index[2], "1D"] = -np.inf
    result = performance.factor_alpha_beta(data, returns, periods_per_year=252)
    assert_allclose(result.loc["beta"], [.4, .4])
    assert_allclose(result.loc["Ann. alpha"], [1.001**252 - 1] * 2)
