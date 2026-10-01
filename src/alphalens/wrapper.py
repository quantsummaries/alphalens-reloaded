#!/usr/bin/env python

# Wrapper of the main functionalities of factor analysis with customizations.

import inspect
import os

import warnings

# Suppress the specific warning from Alphalens
warnings.filterwarnings("ignore", message="'freq' not set in factor_data index: assuming business day")

import pandas as pd

import alphalens


def call_with_matching_args(func, *args, **kwargs):
    """Filters kwargs to only those accepted by func, keeping all positional args."""
    sig = inspect.signature(func)
    valid_keys = sig.parameters.keys()
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}

    return func(*args, **filtered_kwargs)

def return_analysis_wrapper(data: pd.DataFrame,
                            long_short: bool = True,
                            group_neutral: bool = False,
                            by_group: bool = False,
                            tear_sheet_filepath: str = None) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens return analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        long_short (bool, optional): When True, forward returns are demeaned across the full universe so the tear sheet
            evaluates a long/short factor portfolio rather than a raw long-only one. This affects the calculation
            of return-based statistics, and usually the labeling/presentation too. Additionally, long_short -> demeaned
            in factor_weights(...) -> changes whether factor values are demeaned before normalization. Defaults to True.
        group_neutral (bool, optional): When True, demean forward returns by group before computing mean return by
            quantile, so that the result reflects factor skill beyond group-level effects. Additionally,
            group_neutral -> group_adjust in factor_weights(...) -> changes whether weights are built/normalized in a
            group-neutral way. Defaults to False.
        by_group (bool): If True, display graphs separately for each group.
        tear_sheet_filepath (str): File path to save the tear sheet. Do not save if None.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing mean / std error return by quantile and standard error by quantile data frames.
    """
    # data frames indexed by quantiles, with columns being the average forward returns or standard error of
    # average forward returns
    mean_return_by_q, std_err_by_q = alphalens.performance.mean_return_by_quantile(factor_data=data,
                                                                                   by_date=False,
                                                                                   by_group=by_group,
                                                                                   demeaned=long_short,
                                                                                   group_adjust=group_neutral
                                                                                   )

    if tear_sheet_filepath:
        rtrns_tbl = alphalens.tears.create_returns_tear_sheet(factor_data=data,
                                                              long_short=long_short,
                                                              group_neutral=group_neutral,
                                                              by_group=by_group,
                                                              return_df=True,
                                                              save_file=tear_sheet_filepath)
        print(f"\n*** Returns tear sheet saved to {tear_sheet_filepath}")

    return {'mean_return_by_q': mean_return_by_q,
            'std_err_by_q': std_err_by_q}

def information_analysis_wrapper(data: pd.DataFrame,
                                 group_neutral: bool = False,
                                 by_group: bool = False,
                                 tear_sheet_filepath: str = None) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens information analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        group_neutral (bool): Demean forward returns by group before computing IC, so that the result reflects factor
            skill beyond group-level effects and ICs across groups can be compared. Defaults to False as forward
            returns are often residual returns, which are already group-neutral. Defaults to False.
        by_group (bool): Whether to compute IC statistics separately for each group instead of only one pooled summary
            across all assets. It does not change the IC computation method; it changes how results are broken out and
            displayed. Defaults to False.
        tear_sheet_filepath (str): File path to save the tear sheet. Do not save if None.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing information coefficient and rank IC data frames.
    """

    # spearman correlation
    daily_ic_spearman = alphalens.performance.factor_information_coefficient(factor_data=data,
                                                                             group_adjust=group_neutral,
                                                                             by_group=by_group,
                                                                             ic_type='spearman')
    ic_spearman = alphalens.plotting.plot_information_table(daily_ic_spearman.dropna(),
                                                            return_df=True,
                                                            as_figure=False,
                                                            ic_type='spearman')

    # pearson correlation
    daily_ic_pearson = alphalens.performance.factor_information_coefficient(factor_data=data,
                                                                            group_adjust=group_neutral,
                                                                            by_group=by_group,
                                                                            ic_type='pearson')
    ic_pearson = alphalens.plotting.plot_information_table(daily_ic_pearson.dropna(),
                                                           return_df=True,
                                                           as_figure=False,
                                                           ic_type='pearson')

    # tear sheet
    if tear_sheet_filepath:
        ic_tble = alphalens.tears.create_information_tear_sheet(factor_data=data,
                                                                group_neutral=group_neutral,
                                                                by_group=by_group,
                                                                return_df=True,
                                                                save_file=tear_sheet_filepath)
        print(f"\n*** Information tear sheet saved to {tear_sheet_filepath}")

    return {'ic_spearman': ic_spearman.T,
            'ic_pearson': ic_pearson.T}

def turnover_analysis_wrapper(data: pd.DataFrame,
                              turnover_period: int,
                              period_unit: str,
                              tear_sheet_filepath: str = None) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens turnover analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        turnover_period (int): Number of periods for turnover analysis.
        period_unit (str): Unit of time for turnover analysis (e.g., 'D' for days, 'W' for weeks, 'M' for months).
        tear_sheet_filepath (str): File path to save the tear sheet. Do not save if None.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing turnover data frames.
    """
    # Calculate turnover
    quantile_factor = data['factor_quantile']

    quantile_turnover = pd.concat([alphalens.performance.quantile_turnover(quantile_factor=quantile_factor,
                                                                           quantile=q,
                                                                           period=turnover_period)
                                   for q in range(1, int(quantile_factor.max()) + 1)],
                                  axis=1)

    factor_autocorr = alphalens.performance.factor_rank_autocorrelation(factor_data=data,
                                                                        period=turnover_period)

    if tear_sheet_filepath:
        alphalens.tears.create_turnover_tear_sheet(factor_data=data,
                                                   turnover_periods=[f"{turnover_period}{period_unit}"],
                                                   return_df=True,
                                                   save_file=tear_sheet_filepath)
        print(f"\n*** Turnover tear sheet saved to {tear_sheet_filepath}")

    return {'turnover': quantile_turnover,
            'factor_autocorr': factor_autocorr}

def full_tear_sheet_wrapper(data: pd.DataFrame,
                            factors: list[str],
                            fwd_rtrn_cols: list[str],
                            output_dir: str,
                            long_short: bool = True,
                            group_neutral: bool = False,
                            by_group: bool = False,
                            turnover_period: int = 1,
                            period_unit: str = 'D') -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens full tear sheet function.
    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        factors (list[str]): List of factor column names to analyze.
        fwd_rtrn_cols (list[str]): List of forward return column names to analyze.
        output_dir (str): Directory to save the tear sheets. Each factor will have its own subdirectory.
        long_short (bool, optional): Whether to perform long-short analysis. When True, returns are demeaned across
            the full universe so the tear sheet evaluates a long/short factor portfolio rather than a raw long-only one.
            This affects the calculation of return-based statistics, and usually the labeling/presentation too.
            Additionally, long_short -> demeaned in factor_weights(...) -> changes whether factor values are demeaned
            before normalization. Defaults to True.
        group_neutral (bool, optional): Demean forward returns by group before computing IC, so that the result reflects factor
            skill beyond group-level effects and ICs across groups can be compared. Defaults to False as forward
            returns are often residual returns, which are already group-neutral. Additionally,
            group_neutral -> group_adjust in factor_weights(...) -> changes whether weights are built/normalized in a
            group-neutral way. Defaults to False.
        by_group (bool, optional): Whether to compute IC statistics separately for each group instead of only one pooled summary
            across all assets. It does not change the IC computation method; it changes how results are broken out and
            displayed. Defaults to False.
        turnover_period (int, optional): Number of periods for turnover analysis. Defaults to 1.
        period_unit (str, optional): Unit of time for turnover analysis. Defaults to 'D'.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing information coefficient, return analysis, and turnover data frames for each factor.
    """
    result = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if 'date' not in data.columns or 'asset' not in data.columns:
        raise ValueError("Data must contain 'date' and 'asset' columns.")

    data = data.set_index(['date', 'asset']).sort_index()

    assert sorted(alphalens.utils.get_forward_returns_columns(data.columns)) == sorted(fwd_rtrn_cols), "Forward return columns in data do not match fwd_rtrn_cols."

    # information coefficient analysis
    essential_cols = fwd_rtrn_cols
    if 'group' in data.columns:
        essential_cols.append('group')

    ic_spearman_list = []
    ic_pearson_list = []
    for f in factors:
        df = data[essential_cols + [f]].copy()
        df = df.rename(columns={f: 'factor'})

        ic_tear_sheet = os.path.join(output_dir, f"ic_tear_sheet_{f}.png")
        ic_result = alphalens.wrapper.information_analysis_wrapper(data=df,
                                                                   group_neutral=group_neutral,
                                                                   by_group=by_group,
                                                                   tear_sheet_filepath=ic_tear_sheet)
        ic_result['ic_spearman'].insert(0, 'factor', f)
        ic_result['ic_pearson'].insert(0, 'factor', f)
        ic_spearman_list.append(ic_result['ic_spearman'])
        ic_pearson_list.append(ic_result['ic_pearson'])

    result['ic_spearman'] = pd.concat(ic_spearman_list, axis=0)
    result['ic_pearson'] = pd.concat(ic_pearson_list, axis=0)

    # return & turnover analysis
    fwd_rtrn_data = data[fwd_rtrn_cols].copy()
    if 'group' in data.columns:
        grp_by_series = data['group']
    else:
        grp_by_series = None

    mean_return_by_q_list = []
    std_err_by_q_list = []
    turnover_list = []
    factor_autocorr_list = []
    for f in factors:
        df = data[[f]].copy()
        df = df.rename(columns={f: 'factor'})

        clean_data = alphalens.utils.get_clean_factor(factor=df,
                                                      forward_returns=fwd_rtrn_data,
                                                      groupby=grp_by_series,
                                                      binning_by_group=True if 'group' in df.columns else False,
                                                      quantiles=5,
                                                      bins=None)

        rtrn_tear_sheet = os.path.join(output_dir, f"rtrn_tear_sheet_{f}.png")
        rtrn_result = alphalens.wrapper.return_analysis_wrapper(data=clean_data,
                                                                long_short=long_short,
                                                                group_neutral=group_neutral,
                                                                by_group=by_group,
                                                                tear_sheet_filepath=rtrn_tear_sheet)
        rtrn_result['mean_return_by_q'].insert(0, 'factor', f)
        rtrn_result['std_err_by_q'].insert(0, 'factor', f)
        mean_return_by_q_list.append(rtrn_result['mean_return_by_q'])
        std_err_by_q_list.append(rtrn_result['std_err_by_q'])

        turnover_tear_sheet = os.path.join(output_dir, f"turnover_tear_sheet_{f}.png")
        turnover_result = alphalens.wrapper.turnover_analysis_wrapper(data=clean_data,
                                                                      turnover_period=turnover_period,
                                                                      period_unit=period_unit,
                                                                      tear_sheet_filepath=turnover_tear_sheet)
        turnover = turnover_result['turnover'].reset_index(drop=False)
        turnover.insert(0, 'factor', f)
        turnover_list.append(turnover)
        factor_autocorr = turnover_result['factor_autocorr'].reset_index(drop=False)
        factor_autocorr.insert(0, 'factor', f)
        factor_autocorr_list.append(factor_autocorr)

    result['mean_return_by_q'] = pd.concat(mean_return_by_q_list, axis=0)
    result['std_err_by_q'] = pd.concat(std_err_by_q_list, axis=0)
    result['turnover'] = pd.concat(turnover_list, axis=0)
    result['factor_autocorr'] = pd.concat(factor_autocorr_list, axis=0)

    return result
