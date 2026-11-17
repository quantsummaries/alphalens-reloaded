"""Constant decimal signals must not turn rounding noise into exposure."""

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from alphalens import performance, utils


@pytest.mark.parametrize("asset_count", [3, 6, 20])
@pytest.mark.parametrize("group_adjust", [False, True])
@pytest.mark.parametrize("equal_weight", [False, True])
def test_constant_decimal_signals_have_zero_exposure_and_returns(
    asset_count, group_adjust, equal_weight,
):
    dates = pd.bdate_range("2024-01-02", periods=3)
    groups = 2 if group_adjust else 1
    assets = asset_count * groups
    index = pd.MultiIndex.from_product([dates, range(assets)], names=["date", "asset"])
    # Different constants across dates and groups ensure the guard acts within
    # each portfolio-construction group rather than across the whole panel.
    signal = np.concatenate([
        np.repeat([value, -value] if group_adjust else [value], asset_count)
        for value in [.1, -.3, .3]
    ])
    factor = pd.Series(signal, index=index)
    forward = pd.DataFrame({"1D": np.tile(np.linspace(.01, .02, assets), 3)}, index=index)
    groupby = pd.Series(np.tile(np.repeat(range(groups), asset_count), 3), index=index)
    clean = utils.get_clean_factor(factor, forward, groupby=groupby, quantiles=None, bins=5)
    weights = performance.factor_weights(
        clean, demeaned=True, group_adjust=group_adjust, equal_weight=equal_weight,
    )
    assert_allclose(weights, 0, atol=0)
    returns = performance.factor_returns(
        clean, demeaned=True, group_adjust=group_adjust, equal_weight=equal_weight,
    )
    assert_allclose(returns, 0, atol=0)
    # Constant signed signals remain invested when demeaning is disabled.
    long_only_weights = performance.factor_weights(
        clean, demeaned=False, group_adjust=group_adjust, equal_weight=equal_weight,
    )
    assert_allclose(long_only_weights.abs().groupby(level="date").sum(), 1)


@pytest.mark.parametrize("scale", [1., 1e-14])
@pytest.mark.parametrize("group_adjust", [False, True])
def test_nonconstant_factor_weights_preserve_small_signals(scale, group_adjust):
    dates = pd.bdate_range("2024-01-02", periods=2)
    index = pd.MultiIndex.from_product([dates, range(8)], names=["date", "asset"])
    frame = pd.DataFrame({
        "factor": np.tile([-3., -1., 1., 3.], 4) * scale,
        "group": np.tile(np.repeat(["A", "B"], 4), 2),
    }, index=index)
    weights = performance.factor_weights(frame, demeaned=True, group_adjust=group_adjust)
    expected = np.tile([-.375, -.125, .125, .375], 4) / 2
    assert_allclose(weights, expected)
    assert_allclose(weights.groupby(level="date").sum(), 0, atol=1e-15)
    assert_allclose(weights.abs().groupby(level="date").sum(), 1)
