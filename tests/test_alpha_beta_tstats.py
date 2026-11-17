"""Regression inference must survive annualization and return-table rendering."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from alphalens import performance, plotting, tears, utils


ROWS = ["Ann. alpha", "t-stat(alpha)", "beta", "t-stat(beta)"]


@pytest.mark.parametrize("as_series", [False, True])
@pytest.mark.parametrize("periods_per_year", [126, 252])
def test_tstats_match_ols_definition_and_are_not_annualized(as_series, periods_per_year):
    dates = pd.bdate_range("2024-01-02", periods=24)
    market = np.linspace(-.025, .025, len(dates))
    market[3] = np.nan
    signal_return = .001 + .4 * market + np.random.default_rng(42).normal(0, .002, len(dates))
    signal_return[8] = np.nan
    index = pd.MultiIndex.from_product([dates, [1, 2]], names=["date", "asset"])
    horizons = ["1D"] if as_series else ["1D", "5h50m", "1D5h50m"]
    frame = pd.DataFrame({col: np.repeat(market, 2) for col in horizons}, index=index)
    returns = pd.DataFrame({col: signal_return * (i + 1) for i, col in enumerate(horizons)}, index=dates)
    supplied = returns["1D"].copy() if as_series else returns
    actual = performance.factor_alpha_beta(frame, supplied, periods_per_year=periods_per_year)
    assert actual.index.tolist() == ROWS
    for col in horizons:
        y = returns[col].to_numpy()
        valid = np.isfinite(market) & np.isfinite(y)
        x = np.column_stack([np.ones(valid.sum()), market[valid]])
        # Independent OLS definition: coefficient / standard error, after dropping NaNs.
        coefficients = np.linalg.lstsq(x, y[valid], rcond=None)[0]
        residuals = y[valid] - x @ coefficients
        variance = residuals @ residuals / (len(residuals) - 2)
        standard_errors = np.sqrt(np.diag(variance * np.linalg.inv(x.T @ x)))
        assert_allclose(actual.loc[["t-stat(alpha)", "t-stat(beta)"], col], coefficients / standard_errors)
        assert_allclose(actual.loc["Ann. alpha", col], (1 + coefficients[0]) ** periods_per_year - 1)
        assert_allclose(actual.loc["beta", col], coefficients[1])
    other = performance.factor_alpha_beta(frame, supplied, periods_per_year=63)
    pd.testing.assert_frame_equal(
        actual.loc[["t-stat(alpha)", "t-stat(beta)"]],
        other.loc[["t-stat(alpha)", "t-stat(beta)"]],
    )


def test_missing_intercept_slope_pair_returns_four_nan_rows():
    dates = pd.bdate_range("2024-01-02", periods=5)
    index = pd.MultiIndex.from_product([dates, [1, 2]], names=["date", "asset"])
    frame = pd.DataFrame({"1D": .01}, index=index)
    returns = pd.DataFrame({"1D": np.arange(5) * .001}, index=dates)
    result = performance.factor_alpha_beta(frame, returns)
    assert result.index.tolist() == ROWS
    assert result["1D"].isna().all()


def test_tstats_with_no_residual_degrees_of_freedom_are_nan():
    dates = pd.bdate_range("2024-01-02", periods=2)
    index = pd.MultiIndex.from_product([dates, [1, 2]], names=["date", "asset"])
    frame = pd.DataFrame({"1D": np.repeat([-.01, .01], 2)}, index=index)
    returns = pd.DataFrame({"1D": [-.003, .005]}, index=dates)
    result = performance.factor_alpha_beta(frame, returns)
    assert_allclose(result.loc["beta", "1D"], .4)
    assert result.loc[["t-stat(alpha)", "t-stat(beta)"], "1D"].isna().all()


@pytest.mark.parametrize("tables_as_figures", [False, True])
def test_return_table_displays_both_tstats(tables_as_figures, capsys):
    alpha_beta = pd.DataFrame({"1D": [.025, 2.5, -.5, -3.]}, index=ROWS)
    means = pd.DataFrame({"1D": [-.0001, .0002]}, index=[1, 2])
    spread = pd.DataFrame({"1D": [.00015]})
    figure, axis = plt.subplots()
    try:
        table = plotting.plot_returns_table(
            alpha_beta, means, spread, tables_as_figures=tables_as_figures, ax=axis,
        )
        assert table.index.tolist()[:4] == ROWS
        assert len(table) == 7
        assert table.loc["t-stat(alpha)", "1D"] == 2.5
        assert table.loc["t-stat(beta)", "1D"] == -3.
        if tables_as_figures:
            labels = [cell.get_text().get_text() for cell in axis.tables[0].get_celld().values()]
            assert "t-stat(alpha)" in labels
            assert "t-stat(beta)" in labels
        else:
            output = capsys.readouterr().out
            assert "t-stat(alpha)" in output
            assert "t-stat(beta)" in output
    finally:
        plt.close(figure)


def test_saved_return_tear_sheet_includes_tstats(tmp_path, monkeypatch):
    rng = np.random.default_rng(42)
    index = pd.MultiIndex.from_product(
        [pd.bdate_range("2024-01-02", periods=12), range(10)], names=["date", "asset"],
    )
    signal = pd.Series(rng.normal(size=len(index)), index=index)
    forward = pd.DataFrame({"1D": rng.normal(0, .01, len(index))}, index=index)
    clean = utils.get_clean_factor(signal, forward, quantiles=2)
    displayed = []
    original = plotting._plot_summary_table

    def capture(summary, *args, **kwargs):
        displayed.append(summary.copy())
        return original(summary, *args, **kwargs)

    monkeypatch.setattr(plotting, "_plot_summary_table", capture)
    path = tmp_path / "returns.png"
    table = tears.create_returns_tear_sheet(
        clean, save_file=str(path), periods_per_year=252, equal_weight=True,
    )
    assert path.is_file()
    assert len(displayed) == 1
    pd.testing.assert_frame_equal(table, displayed[0])
    assert table.index.tolist()[:4] == ROWS
    assert np.isfinite(table.loc[["t-stat(alpha)", "t-stat(beta)"], "1D"]).all()
