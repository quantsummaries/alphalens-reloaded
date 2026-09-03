#!/usr/bin/env python

# Wrapper of the main functionalities of factor analysis with customizations.

import inspect

import pandas as pd

import alphalens


def call_with_matching_args(func, *args, **kwargs):
    """Filters kwargs to only those accepted by func, keeping all positional args."""
    sig = inspect.signature(func)
    valid_keys = sig.parameters.keys()
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}

    return func(*args, **filtered_kwargs)

def return_analysis_wrapper(data: pd.DataFrame,
                            tear_sheet_filepath: str) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens return analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        tear_sheet_filepath (str): File path to save the tear sheet. Do not save if None.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing mean / std error return by quantile and standard error by quantile data frames.
    """
    # data frames indexed by quantiles, with columns being the average forward returns or standard error of
    # average forward returns
    mean_return_by_q, std_err_by_q = alphalens.performance.mean_return_by_quantile(factor_data=data,
                                                                                   by_date=False,
                                                                                   by_group=False,
                                                                                   demeaned=True,
                                                                                   group_adjust=False
                                                                                   )

    if tear_sheet_filepath:
        rtrns_tbl = alphalens.tears.create_returns_tear_sheet(factor_data=data,
                                                              long_short=True,
                                                              group_neutral=False,
                                                              by_group=False,
                                                              return_df=True,
                                                              save_file=tear_sheet_filepath)
        print(f"\nReturns tear sheet saved to {tear_sheet_filepath}\n")

    return {'mean_return_by_q': mean_return_by_q,
            'std_err_by_q': std_err_by_q}

def information_analysis_wrapper(data: pd.DataFrame,
                                 group_adjust: bool = False,
                                 by_group: bool = False,
                                 tear_sheet_filepath: str = None) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens information analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        group_adjust (bool): Demean forward returns by group before computing IC.
        by_group (bool): If True, compute period wise IC separately for each group.
        tear_sheet_filepath (str): File path to save the tear sheet. Do not save if None.
    Returns:
        dict[str, pd.DataFrame]: Dictionary containing information coefficient and rank IC data frames.
    """

    # spearman correlation
    daily_ic_spearman = alphalens.performance.factor_information_coefficient(factor_data=data,
                                                                             group_adjust=group_adjust,
                                                                             by_group=by_group,
                                                                             ic_type='spearman')
    ic_spearman = alphalens.plotting.plot_information_table(daily_ic_spearman.dropna(),
                                                            return_df=True,
                                                            as_figure=False,
                                                            ic_type='spearman')

    # pearson correlation
    daily_ic_pearson = alphalens.performance.factor_information_coefficient(factor_data=data,
                                                                            group_adjust=group_adjust,
                                                                            by_group=by_group,
                                                                            ic_type='pearson')
    ic_pearson = alphalens.plotting.plot_information_table(daily_ic_pearson.dropna(),
                                                           return_df=True,
                                                           as_figure=False,
                                                           ic_type='pearson')

    # tear sheet
    if tear_sheet_filepath:
        ic_tble = alphalens.tears.create_information_tear_sheet(factor_data=data,
                                                                group_neutral=group_adjust,
                                                                by_group=by_group,
                                                                return_df=True,
                                                                save_file=tear_sheet_filepath)
        print(f"\nInformation tear sheet saved to {tear_sheet_filepath}\n")

    return {'ic_spearman': ic_spearman.T,
            'ic_pearson': ic_pearson.T}

def turnover_analysis_wrapper(data: pd.DataFrame,
                              turnover_period: int,
                              period_unit: str,
                              tear_sheet_filepath: str) -> dict[str, pd.DataFrame]:
    """Wrapper for alphalens turnover analysis functions.

    Args:
        data (pd.DataFrame): Factor data in the format expected by alphalens.
        turnover_period (int): Number of period for turnover analysis.
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
        print(f"\nTurnover tear sheet saved to {tear_sheet_filepath}\n")

    return {'turnover': quantile_turnover,
            'factor_autocorr': factor_autocorr}
