"""Portfolio weighting must agree across text reports and saved tear sheets."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from alphalens import performance, plotting, utils, wrapper


@pytest.mark.parametrize("signals,expected", [
    ([1., 2., 3., 100.], [-.25, -.25, .25, .25]),
    ([1., 2., 2., 4.], [-.5, 0., 0., .5]),
    ([2., 2., 2., 2.], [0., 0., 0., 0.]),
    ([0., 0., 1.], [0., 0., 1.]),
    ([-1., 0., 0.], [-1., 0., 0.]),
])
def test_equal_weight_median_ties_and_degenerate_legs(signals, expected):
    index = pd.MultiIndex.from_product(
        [pd.to_datetime(["2024-01-02"]), range(len(signals))],
        names=["date", "asset"],
    )
    frame = pd.DataFrame({
        "factor": signals, "1D": np.arange(1, len(signals) + 1) / 100.,
    }, index=index)
    weights = performance.factor_weights(frame, demeaned=True, equal_weight=True)
    assert_allclose(weights, expected)
    returns = performance.factor_returns(frame, demeaned=True, equal_weight=True)
    assert_allclose(returns["1D"], np.dot(expected, frame["1D"]))


@pytest.mark.parametrize("mode", ["text", "saved", "full_wrapper"])
@pytest.mark.parametrize("weighting", ["default", "factor", "equal"])
def test_weighting_reaches_portfolio_statistics_and_plot(
    mode, weighting, tmp_path, monkeypatch,
):
    rng = np.random.default_rng(42)
    index = pd.MultiIndex.from_product(
        [pd.bdate_range("2024-01-02", periods=12), range(8)],
        names=["date", "asset"],
    )
    data = pd.DataFrame({
        "signal": np.tile([-3., -2., -1., 0., 1., 2., 3., 100.], 12),
        "1D": rng.normal(0, .01, len(index)),
    }, index=index)
    clean = utils.get_clean_factor(data["signal"], data[["1D"]], quantiles=2)
    equal_weight = weighting == "equal"
    expected_returns = performance.factor_returns(clean, equal_weight=equal_weight)
    expected_table = performance.factor_alpha_beta(
        clean, expected_returns, periods_per_year=126,
    )
    factor_returns = performance.factor_returns(clean, equal_weight=False)
    equal_returns = performance.factor_returns(clean, equal_weight=True)
    assert not np.allclose(factor_returns, equal_returns)
    alpha_calls = []
    plots = []
    original_alpha = performance.factor_alpha_beta
    original_plot = plotting.plot_cumulative_returns

    def capture_alpha(factor_data, returns=None, *args, **kwargs):
        pd.testing.assert_frame_equal(returns, expected_returns)
        result = original_alpha(factor_data, returns, *args, **kwargs)
        pd.testing.assert_frame_equal(result, expected_table)
        alpha_calls.append(result)
        return result

    def capture_plot(returns, *args, **kwargs):
        pd.testing.assert_series_equal(returns, expected_returns["1D"])
        prefix = "Equal Weighted " if equal_weight else "Factor Weighted "
        assert kwargs["title"].startswith(prefix)
        plots.append(kwargs["title"])
        return original_plot(returns, *args, **kwargs)

    monkeypatch.setattr(performance, "factor_alpha_beta", capture_alpha)
    monkeypatch.setattr(plotting, "plot_cumulative_returns", capture_plot)
    # Full-wrapper tests keep the real return report and isolate unrelated reports.
    monkeypatch.setattr(wrapper, "information_analysis_wrapper", lambda **kwargs: {
        f"ic_{kind}": pd.DataFrame({"1D": [.1]}, index=[f"IC Mean ({kind})"])
        for kind in ["spearman", "pearson"]
    })
    monkeypatch.setattr(wrapper, "turnover_analysis_wrapper", lambda **kwargs: {
        "turnover": pd.DataFrame({1: [.1]}),
        "factor_autocorr": pd.Series([.2]),
    })
    options = {} if weighting == "default" else {"equal_weight": equal_weight}
    if mode == "full_wrapper":
        wrapper.full_tear_sheet_wrapper(
            data, ["signal"], ["1D"], str(tmp_path), quantiles=2,
            periods_per_year=126, **options,
        )
        assert (tmp_path / "rtrn_tear_sheet_signal.png").is_file()
    else:
        wrapper.return_analysis_wrapper(
            clean, periods_per_year=126, tables_as_figures=False,
            tear_sheet_filepath=str(tmp_path / "returns.png") if mode == "saved" else None,
            **options,
        )
        if mode == "saved":
            assert (tmp_path / "returns.png").is_file()
    assert len(alpha_calls) == 1
    assert len(plots) == (0 if mode == "text" else 1)
