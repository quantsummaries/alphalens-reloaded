"""Annualize alpha from an explicit trading schedule through public entry points."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from alphalens import performance, tears, utils, wrapper


@pytest.fixture
def data():
    rng = np.random.default_rng(42)
    index = pd.MultiIndex.from_product(
        [pd.bdate_range('2024-01-02', periods=20), range(10)], names=['date', 'asset']
    )
    frame = pd.DataFrame({'signal': rng.normal(size=len(index))}, index=index)
    frame['5h50m'] = .001 * frame['signal'] + rng.normal(0, .01, len(index))
    return frame


@pytest.mark.parametrize('override', [None, 252, 126, {'5h50m': 252, '1D': 252, '1D5h50m': 126}])
def test_known_alpha_and_beta(override):
    dates = pd.bdate_range('2024-01-02', periods=4)
    index = pd.MultiIndex.from_product([dates, [1, 2]], names=['date', 'asset'])
    market = np.array([.01, -.01, .02, -.02])
    columns = ['5h50m', '1D', '1D5h50m']
    frame = pd.DataFrame({col: np.repeat(market, 2) for col in columns}, index=index)
    returns = pd.DataFrame({col: .001 + .5 * market for col in columns}, index=dates)
    result = performance.factor_alpha_beta(frame, returns, periods_per_year=override)
    for col in columns:
        exponent = (pd.Timedelta(days=252) / pd.Timedelta(col) if override is None
                    else override[col] if isinstance(override, dict) else override)
        assert_allclose(result.loc['Ann. alpha', col], 1.001**exponent - 1)
        assert_allclose(result.loc['beta', col], .5)


@pytest.mark.parametrize('override', [0, -1, float('nan'), float('inf'), True, '252', {}, {'5h50m': 0}])
def test_invalid_annualization_rejected(data, override):
    with pytest.raises(ValueError, match='periods_per_year'):
        performance.factor_alpha_beta(data.rename(columns={'signal': 'factor'}), periods_per_year=override)


@pytest.mark.parametrize('mode', ['text', 'saved', 'full_wrapper', 'full_tear', 'summary'])
def test_public_entry_points_forward_annualization(data, tmp_path, monkeypatch, mode):
    if mode == 'full_tear':
        # The stock full tear sheet requires whole-day horizons for turnover.
        data = data.rename(columns={'5h50m': '1D'})
    horizon = '1D' if mode == 'full_tear' else '5h50m'
    clean = utils.get_clean_factor(data['signal'], data[[horizon]], quantiles=2)
    expected = performance.factor_alpha_beta(clean, periods_per_year=126)
    actual = []
    original = performance.factor_alpha_beta

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        actual.append(result)
        return result

    monkeypatch.setattr(performance, 'factor_alpha_beta', capture)
    if mode == 'full_wrapper':
        wrapper.full_tear_sheet_wrapper(
            data, ['signal'], ['5h50m'], str(tmp_path), quantiles=2, periods_per_year=126,
        )
    elif mode == 'full_tear':
        tears.create_full_tear_sheet(clean, periods_per_year=126)
    elif mode == 'summary':
        tears.create_summary_tear_sheet(clean, periods_per_year=126)
    else:
        wrapper.return_analysis_wrapper(
            clean, periods_per_year=126,
            tear_sheet_filepath=str(tmp_path / 'returns.png') if mode == 'saved' else None,
        )
    assert len(actual) == 1
    pd.testing.assert_frame_equal(actual[0], expected)
    if mode == 'saved':
        assert (tmp_path / 'returns.png').exists()
