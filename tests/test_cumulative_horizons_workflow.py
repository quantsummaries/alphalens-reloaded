"""Every supplied horizon gets portfolio and five-quantile cumulative curves."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from alphalens import performance, plotting, tears, utils


@pytest.mark.parametrize('horizons', [
    ['5h50m'], ['1D'], ['1D5h50m'], ['5h50m', '1D', '1D5h50m'],
])
@pytest.mark.parametrize('tables_as_figures', [True, False])
def test_cumulative_curves_for_all_horizons(horizons, tables_as_figures, tmp_path, monkeypatch):
    rng = np.random.default_rng(42)
    # Every other trading session keeps even the longest horizon non-overlapping.
    dates = pd.bdate_range('2024-01-02', periods=20)[::2]
    index = pd.MultiIndex.from_product([dates, range(20)], names=['date', 'asset'])
    factor = pd.Series(rng.normal(size=len(index)), index=index)
    forward = pd.DataFrame({
        period: .001 * factor + rng.normal(0, .01, len(index))
        for period in horizons
    }, index=index)
    clean = utils.get_clean_factor(factor, forward, quantiles=5)
    portfolio_returns = performance.factor_returns(clean)
    quantile_returns, _ = performance.mean_return_by_quantile(clean, by_date=True)
    portfolio_calls = []
    quantile_calls = []
    plot_portfolio = plotting.plot_cumulative_returns
    plot_quantiles = plotting.plot_cumulative_returns_by_quantile

    def capture_portfolio(returns, period, **kwargs):
        ax = plot_portfolio(returns, period, **kwargs)
        portfolio_calls.append(period)
        assert period in ax.get_title()
        assert_allclose(ax.lines[0].get_ydata(), (1 + portfolio_returns[period]).cumprod())
        return ax

    def capture_quantiles(returns, period, **kwargs):
        ax = plot_quantiles(returns, period, **kwargs)
        quantile_calls.append(period)
        assert period in ax.get_title()
        # Five quantile curves plus the horizontal baseline at one.
        assert len(ax.lines) == 6
        expected = (1 + quantile_returns[period].unstack('factor_quantile')).cumprod()
        for line in ax.lines[:-1]:
            quantile = int(line.get_label())
            assert_allclose(line.get_ydata(), expected[quantile])
        return ax

    monkeypatch.setattr(plotting, 'plot_cumulative_returns', capture_portfolio)
    monkeypatch.setattr(plotting, 'plot_cumulative_returns_by_quantile', capture_quantiles)
    output = tmp_path / 'returns.png'
    table = tears.create_returns_tear_sheet(
        clean, periods_per_year=126, tables_as_figures=tables_as_figures,
        save_file=str(output),
    )
    assert portfolio_calls == horizons
    assert quantile_calls == horizons
    assert table.columns.to_list() == horizons
    assert output.stat().st_size > 0
