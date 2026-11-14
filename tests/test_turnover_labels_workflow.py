"""Sample-interval labels must never change the observation lag in turnover."""

import numpy as np
import pandas as pd
import pytest
import matplotlib.pyplot as plt
from pandas.testing import assert_frame_equal, assert_series_equal

from alphalens import performance, plotting, tears, utils, wrapper


@pytest.fixture
def panel():
    dates = pd.bdate_range('2024-01-02', periods=12)[::2]
    index = pd.MultiIndex.from_product([dates, range(10)], names=['date', 'asset'])
    signal = pd.Series(np.concatenate([np.roll(np.arange(10), i) for i in range(6)]), index=index)
    forward = pd.DataFrame({'1D5h50m': np.random.default_rng(42).normal(0, .01, len(index))}, index=index)
    return utils.get_clean_factor(signal, forward, quantiles=5)


@pytest.mark.parametrize('mode', ['text', 'saved', 'full'])
@pytest.mark.parametrize('tables_as_figures', [False, True])
@pytest.mark.parametrize('label', [None, '2 trading sessions'])
def test_labels_preserve_adjacent_observation_calculations(
    panel, mode, tables_as_figures, label, tmp_path, monkeypatch,
):
    expected_turnover = pd.concat([
        performance.quantile_turnover(panel['factor_quantile'], q, period=1)
        for q in range(1, 6)
    ], axis=1)
    expected_autocorr = performance.factor_rank_autocorrelation(panel, period=1)
    # This data distinguishes adjacent observations from a two-observation lag.
    assert not np.isclose(expected_turnover[1].mean(), performance.quantile_turnover(panel['factor_quantile'], 1, 2).mean())
    assert not np.isclose(expected_autocorr.mean(), performance.factor_rank_autocorrelation(panel, 2).mean())
    labels = None if label is None else {1: label}
    display = '1 observation' if label is None else label
    lags = []
    titles = []
    tables = []
    original_turnover = performance.quantile_turnover
    original_autocorr = performance.factor_rank_autocorrelation
    original_table = plotting.plot_turnover_table
    original_turnover_plot = plotting.plot_top_bottom_quantile_turnover
    original_autocorr_plot = plotting.plot_factor_rank_auto_correlation

    def turnover(quantile_factor, quantile, period=1):
        lags.append(period)
        return original_turnover(quantile_factor, quantile, period)

    def autocorr(factor_data, period=1):
        lags.append(period)
        return original_autocorr(factor_data, period)

    def table(*args, **kwargs):
        result = original_table(*args, **kwargs)
        for frame in result:
            assert frame.columns.to_list() == [display]
        tables.append(result)
        return result

    def turnover_plot(*args, **kwargs):
        ax = original_turnover_plot(*args, **kwargs)
        titles.append(ax.get_title())
        assert display in ax.get_title()
        return ax

    def autocorr_plot(*args, **kwargs):
        ax = original_autocorr_plot(*args, **kwargs)
        titles.append(ax.get_title())
        assert display in ax.get_title()
        return ax

    monkeypatch.setattr(performance, 'quantile_turnover', turnover)
    monkeypatch.setattr(performance, 'factor_rank_autocorrelation', autocorr)
    monkeypatch.setattr(plotting, 'plot_turnover_table', table)
    monkeypatch.setattr(plotting, 'plot_top_bottom_quantile_turnover', turnover_plot)
    monkeypatch.setattr(plotting, 'plot_factor_rank_auto_correlation', autocorr_plot)
    if mode == 'full':
        # Isolate turnover while exercising the real full-wrapper forwarding path.
        monkeypatch.setattr(wrapper, 'information_analysis_wrapper', lambda **kwargs: {
            f'ic_{kind}': pd.DataFrame({'1D5h50m': [.1]}, index=[f'IC Mean ({kind})'])
            for kind in ['spearman', 'pearson']
        })
        monkeypatch.setattr(wrapper, 'return_analysis_wrapper', lambda **kwargs: {
            key: pd.DataFrame({'1D5h50m': [.01]})
            for key in ['mean_return_by_q', 'std_err_by_q']
        })
        result = wrapper.full_tear_sheet_wrapper(
            panel.rename(columns={'factor': 'signal'}).drop(columns='factor_quantile'),
            factors=['signal'], fwd_rtrn_cols=['1D5h50m'], output_dir=str(tmp_path),
            tables_as_figures=tables_as_figures, turnover_period_labels=labels,
        )
        actual_turnover = result['turnover'].drop(columns='factor').set_index('date')
        actual_autocorr = result['factor_autocorr'].set_index('date')[1]
        assert (tmp_path / 'turnover_tear_sheet_signal.png').is_file()
    else:
        result = wrapper.turnover_analysis_wrapper(
            panel, turnover_period=1, period_unit='D', tables_as_figures=tables_as_figures,
            tear_sheet_filepath=str(tmp_path / 'turnover.png') if mode == 'saved' else None,
            turnover_period_labels=labels,
        )
        actual_turnover = result['turnover']
        actual_autocorr = result['factor_autocorr']
        if mode == 'saved':
            assert (tmp_path / 'turnover.png').is_file()
    assert_frame_equal(actual_turnover, expected_turnover, check_freq=False, check_column_type=False)
    assert_series_equal(actual_autocorr, expected_autocorr, check_freq=False)
    assert set(lags) == {1}
    assert len(tables) == 1
    assert len(titles) == (0 if mode == 'text' else 2)


@pytest.mark.parametrize('labels', [
    None,
    {1: '2 sessions', 2: '4 sessions'},
    {1: '2 sessions'},
])
def test_direct_tear_sheet_supports_distinct_labels_for_multiple_lags(panel, tmp_path, labels):
    expected_labels = ['1 observation', '2 observations'] if labels is None else [
        labels[1], labels.get(2, '2 observations'),
    ]
    turnover, autocorr = tears.create_turnover_tear_sheet(
        panel, turnover_periods=['1D', '2D'],
        turnover_period_labels=labels,
        save_file=str(tmp_path / 'multiple_lags.png'),
    )
    assert turnover.columns.to_list() == expected_labels
    assert autocorr.columns.to_list() == expected_labels
    assert np.isclose(turnover.loc['Quantile 1 Mean Turnover ', expected_labels[0]], .5)
    assert np.isclose(turnover.loc['Quantile 1 Mean Turnover ', expected_labels[1]], 1.)
    for period, label in zip([1, 2], expected_labels):
        assert np.isclose(
            autocorr.loc['Mean Factor Rank Autocorrelation', label],
            performance.factor_rank_autocorrelation(panel, period).mean(),
        )


@pytest.mark.parametrize('tables_as_figures', [False, True])
@pytest.mark.parametrize('labels', [
    {1: '2 sessions', 2: '2 sessions'},
    {1: '2 observations'},
])
@pytest.mark.parametrize('split_lags', [False, True])
def test_table_rejects_conflicting_labels(labels, tables_as_figures, split_lags):
    # Also catch collisions across the two tables when their lag sets differ.
    autocorr = pd.DataFrame({2: [.9]})
    turnover = {1: pd.DataFrame({1: [.2]})}
    if not split_lags:
        autocorr[1] = .1
        turnover[2] = pd.DataFrame({1: [.8]})
    with pytest.raises(ValueError, match='Turnover lags 1 and 2 both resolve to label'):
        plotting.plot_turnover_table(
            autocorr, turnover, tables_as_figures=tables_as_figures,
            period_labels=labels,
        )


def test_plural_observation_labels_in_plot_titles(panel):
    fig, axes = plt.subplots(2)
    try:
        plotting.plot_factor_rank_auto_correlation(
            performance.factor_rank_autocorrelation(panel, 2), period=2, ax=axes[0],
        )
        plotting.plot_top_bottom_quantile_turnover(
            pd.concat([
                performance.quantile_turnover(panel['factor_quantile'], q, 2)
                for q in [1, 5]
            ], axis=1),
            period=2, ax=axes[1],
        )
        assert axes[0].get_title() == '2 observations Period Factor Rank Autocorrelation'
        assert axes[1].get_title() == '2 observations Period Top and Bottom Quantile Turnover'
    finally:
        plt.close(fig)
