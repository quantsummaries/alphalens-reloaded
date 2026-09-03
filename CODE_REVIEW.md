# Alphalens Documentation

## Review Addendum

_Since commit `3cd82b40c5013a12d1b4fa1d37ae9d1d34af2a82`._

### Scope reviewed

- `src/alphalens/performance.py`
- `src/alphalens/plotting.py`
- `src/alphalens/tears.py`
- `src/alphalens/wrapper.py`
- `src/alphalens/__init__.py`
- related tests under `tests/`

### Findings (ordered by severity)

1. **Medium**: `return_df` is effectively ignored in `create_information_tear_sheet(...)` because `plot_information_table(...)` is always called with `as_figure=True`, so the function returns a figure handle rather than a DataFrame.
   - Ref: `src/alphalens/tears.py`
2. **Medium**: `create_turnover_tear_sheet(...)` accepts `return_df` and forwards it to `plot_turnover_table(...)`, but does not return the tables.
   - Ref: `src/alphalens/tears.py`
3. **Low (testing gap)**: `tests/test_wrapper.py` currently has no pytest test functions (`collected 0 items`), so wrapper behavior is not covered by automated tests.
   - Ref: `tests/test_wrapper.py`

### API / behavior changes captured

- `performance.factor_information_coefficient(...)` now supports `ic_type` (`"spearman"` or `"pearson"`).
- `plotting.plot_information_table(...)` now supports `as_figure` and `ic_type` and can return a matplotlib figure.
- Table display helpers explicitly return `None` when not returning DataFrames.
- `tears.create_returns_tear_sheet(...)` supports `return_df` and `save_file` and can save all generated return plots into a single output file.
- `tears.create_information_tear_sheet(...)` and `tears.create_turnover_tear_sheet(...)` now expose `return_df` / `save_file` parameters.
- New top-level wrapper module exposed as `alphalens.wrapper`.

### Documentation updates completed

The following docs were updated to reflect current implementation:

- `docs/performance.md`
- `docs/plotting.md`
- `docs/tears.md`
- `docs/utils.md`
- `docs/wrapper.md`

### Follow-up recommendations

- Align `create_information_tear_sheet(...)` return behavior with its `return_df` parameter intent.
- Return table outputs from `create_turnover_tear_sheet(...)` when `return_df=True`.
- Add real unit tests in `tests/test_wrapper.py` for wrapper function outputs and save-file behavior.

## Table of Contents

- [0 Review Addendum](#review-addendum)
- [1 Overview](#overview)
- [2 alphalens.utils](#alphalensutils)
  - 2.1 Data model used by this module
  - 2.2 Exceptions
  - 2.3 Core workflow
    - [2.3.1 `compute_forward_returns()`](#compute_forward_returnsfactor-prices-periods1-5-10-filter_zscorenone-cumulative_returnstrue)
    - [2.3.2 `get_clean_factor()`](#get_clean_factorfactor-forward_returns-groupbynone-binning_by_groupfalse-quantiles5-binsnone-groupby_labelsnone-max_loss035-zero_awarefalse)
    - [2.3.3 `get_clean_factor_and_forward_returns()`](#get_clean_factor_and_forward_returnsfactor-prices-groupbynone-binning_by_groupfalse-quantiles5-binsnone-periods1-5-10-filter_zscore20-groupby_labelsnone-max_loss035-zero_awarefalse-cumulative_returnstrue)
  - 2.4 Quantization and bucketing
    - [2.4.1 `quantize_factor()`](#quantize_factorfactor_data-quantiles5-binsnone-by_groupfalse-no_raisefalse-zero_awarefalse)
    - [2.4.2 `non_unique_bin_edges_error()`](#non_unique_bin_edges_errorfunc)
  - 2.5 Return and performance helpers
    - [2.5.1 `backshift_returns_series()`](#backshift_returns_seriesseries-n)
    - [2.5.2 `demean_forward_returns()`](#demean_forward_returnsfactor_data-groupernone)
    - [2.5.3 `rate_of_return()`](#rate_of_returnperiod_ret-base_period)
    - [2.5.4 `std_conversion()`](#std_conversionperiod_std-base_period)
  - 2.6 Calendar and time utilities
    - [2.6.1 `infer_trading_calendar()`](#infer_trading_calendarfactor_idx-prices_idx)
    - [2.6.2 `timedelta_to_string()`](#timedelta_to_stringtimedelta)
    - [2.6.3 `timedelta_strings_to_integers()`](#timedelta_strings_to_integerssequence)
    - [2.6.4 `add_custom_calendar_timedelta()`](#add_custom_calendar_timedeltainput-timedelta-freq)
    - [2.6.5 `make_naive_ts()`](#make_naive_tst)
    - [2.6.6 `diff_custom_calendar_timedeltas()`](#diff_custom_calendar_timedeltasstart-end-freq)
  - 2.7 Column detection and display helpers
    - [2.7.1 `get_forward_returns_columns()`](#get_forward_returns_columnscolumns-require_exact_day_multiplefalse)
    - [2.7.2 `print_table()`](#print_tabletable-namenone-fmtnone)
  - 2.8 Error handling helper
    - [2.8.1 `rethrow()`](#rethrowexception-additional_message)
  - 2.9 Practical usage
  - 2.10 Notes
- [3 alphalens.performance](#alphalensperformance)
  - 3.1 Data model used by this module
  - 3.2 Core analysis functions
    - [3.2.1 `factor_information_coefficient()`](#factor_information_coefficientfactor_data-group_adjustfalse-by_groupfalse)
    - [3.2.2 `mean_information_coefficient()`](#mean_information_coefficientfactor_data-group_adjustfalse-by_groupfalse-by_timenone)
  - 3.3 Portfolio weighting and return simulation
    - [3.3.1 `factor_weights()`](#factor_weightsfactor_data-demeanedtrue-group_adjustfalse-equal_weightfalse)
    - [3.3.2 `factor_returns()`](#factor_returnsfactor_data-demeanedtrue-group_adjustfalse-equal_weightfalse-by_assetfalse)
    - [3.3.3 `factor_alpha_beta()`](#factor_alpha_betafactor_data-returnsnone-demeanedtrue-group_adjustfalse-equal_weightfalse)
    - [3.3.4 `cumulative_returns()`](#cumulative_returnsreturns)
    - [3.3.5 `positions()`](#positionsweights-period-freqnone)
  - 3.4 Quantile and bucket analysis
    - [3.4.1 `mean_return_by_quantile()`](#mean_return_by_quantilefactor_data-by_datefalse-by_groupfalse-demeanedtrue-group_adjustfalse)
    - [3.4.2 `compute_mean_returns_spread()`](#compute_mean_returns_spreadmean_returns-upper_quant-lower_quant-std_errnone)
    - [3.4.3 `quantile_turnover()`](#quantile_turnoverquantile_factor-quantile-period1)
    - [3.4.4 `factor_rank_autocorrelation()`](#factor_rank_autocorrelationfactor_data-period1)
  - 3.5 Event-study helpers
    - [3.5.1 `common_start_returns()`](#common_start_returnsfactor-returns-before-after-cumulativefalse-mean_by_datefalse-demean_bynone)
    - [3.5.2 `average_cumulative_return_by_quantile()`](#average_cumulative_return_by_quantilefactor_data-returns-periods_before10-periods_after15-demeanedtrue-group_adjustfalse-by_groupfalse)
  - 3.6 Portfolio simulation outputs
    - [3.6.1 `factor_cumulative_returns()`](#factor_cumulative_returnsfactor_data-period-long_shorttrue-group_neutralfalse-equal_weightfalse-quantilesnone-groupsnone)
    - [3.6.2 `factor_positions()`](#factor_positionsfactor_data-period-long_shorttrue-group_neutralfalse-equal_weightfalse-quantilesnone-groupsnone)
    - [3.6.3 `create_pyfolio_input()`](#create_pyfolio_inputfactor_data-period-capitalnone-long_shorttrue-group_neutralfalse-equal_weightfalse-quantilesnone-groupsnone-benchmark_period1d)
  - 3.7 Dependencies and implementation notes
  - 3.8 Practical usage
- [4 alphalens.plotting](#alphalensplotting)
  - 4.1 Styling and context management
    - [4.1.1 `customize()`](#customizefunc-----decorator)
    - [4.1.2 `plotting_context()`](#plotting_contextcontextnotebook-font_scale15-rcnone)
    - [4.1.3 `axes_style()`](#axes_stylestyledarkgrid-rcnone)
  - 4.2 Data table displays
    - [4.2.1 `plot_returns_table()`](#plot_returns_tablealpha_beta-mean_ret_quantile-mean_ret_spread_quantile-return_dffalse)
    - [4.2.2 `plot_turnover_table()`](#plot_turnover_tableautocorrelation_data-quantile_turnover-return_dffalse)
    - [4.2.3 `plot_information_table()`](#plot_information_tableic_data-return_dffalse)
    - [4.2.4 `plot_quantile_statistics_table()`](#plot_quantile_statistics_tablefactor_data-return_dffalse)
  - 4.3 Information Coefficient visualization
    - [4.3.1 `plot_ic_ts()`](#plot_ic_tsic-axnone)
    - [4.3.2 `plot_ic_hist()`](#plot_ic_histic-axnone)
    - [4.3.3 `plot_ic_qq()`](#plot_ic_qqic-theoretical_distscipystatsnorm-axnone)
    - [4.3.4 `plot_ic_by_group()`](#plot_ic_by_groupic_group-axnone)
    - [4.3.5 `plot_monthly_ic_heatmap()`](#plot_monthly_ic_heatmapmean_monthly_ic-axnone)
  - 4.4 Returns analysis
    - [4.4.1 `plot_quantile_returns_bar()`](#plot_quantile_returns_barmean_ret_by_q-by_groupfalse-ylim_percentilesnone-axnone)
    - [4.4.2 `plot_quantile_returns_violin()`](#plot_quantile_returns_violinreturn_by_q-ylim_percentilesnone-axnone)
    - [4.4.3 `plot_mean_quantile_returns_spread_time_series()`](#plot_mean_quantile_returns_spread_time_seriesmean_returns_spread-std_errnone-bandwidth1-axnone)
    - [4.4.4 `plot_cumulative_returns()`](#plot_cumulative_returnsfactor_returns-period-freqnone-titlenone-axnone)
    - [4.4.5 `plot_cumulative_returns_by_quantile()`](#plot_cumulative_returns_by_quantilequantile_returns-period-freqnone-axnone)
    - [4.4.6 `plot_quantile_average_cumulative_return()`](#plot_quantile_average_cumulative_returnavg_cumulative_returns-by_quantilefalse-std_barfalse-titlenone-axnone)
  - 4.5 Factor characteristics
    - [4.5.1 `plot_factor_rank_auto_correlation()`](#plot_factor_rank_auto_correlationfactor_autocorrelation-period1-axnone)
    - [4.5.2 `plot_top_bottom_quantile_turnover()`](#plot_top_bottom_quantile_turnoverquantile_turnover-period1-axnone)
    - [4.5.3 `plot_events_distribution()`](#plot_events_distributionevents-num_bars50-axnone)
  - 4.6 Constants
    - [4.6.1 `DECIMAL_TO_BPS = 10000`](#decimal_to_bps--10000)
  - 4.7 Dependencies and conventions
  - 4.8 Practical usage
  - 4.9 Notes
- [5 alphalens.tears](#alphalenstears)
  - 5.1 Helper class
    - [5.1.1 `GridFigure`](#gridfigure)
  - 5.2 Tear sheet generators
    - [5.2.1 `create_summary_tear_sheet()`](#create_summary_tear_sheetfactor_data-long_shorttrue-group_neutralfalse)
    - [5.2.2 `create_returns_tear_sheet()`](#create_returns_tear_sheetfactor_data-long_shorttrue-group_neutralfalse-by_groupfalse)
    - [5.2.3 `create_information_tear_sheet()`](#create_information_tear_sheetfactor_data-group_neutralfalse-by_groupfalse)
    - [5.2.4 `create_turnover_tear_sheet()`](#create_turnover_tear_sheetfactor_data-turnover_periodsnone)
    - [5.2.5 `create_full_tear_sheet()`](#create_full_tear_sheetfactor_data-long_shorttrue-group_neutralfalse-by_groupfalse)
    - [5.2.6 `create_event_returns_tear_sheet()`](#create_event_returns_tear_sheetfactor_data-returns-avgretplot5-15-long_shorttrue-group_neutralfalse-std_bartrue-by_groupfalse)
    - [5.2.7 `create_event_study_tear_sheet()`](#create_event_study_tear_sheetfactor_data-returns-avgretplot5-15-rate_of_rettrue-n_bars50)
  - 5.3 Data model
  - 5.4 Dependencies and concepts
  - 5.5 Practical usage
  - 5.6 Notes
- [6 alphalens.wrapper](#alphalenswrapper)
  - 6.1 Input data expectation
  - 6.2 Utility helpers
    - [6.2.1 `ic_autocor_adj()`](#ic_autocor_adjdaily_ic-lag5)
    - [6.2.2 `call_with_matching_args()`](#call_with_matching_argsfunc-args-kwargs)
  - 6.3 Workflow wrappers
    - [6.3.1 `return_analysis_wrapper()`](#return_analysis_wrapperdata-tear_sheet_filepath)
    - [6.3.2 `information_analysis_wrapper()`](#information_analysis_wrapperdata-tear_sheet_filepath)
    - [6.3.3 `turnover_analysis_wrapper()`](#turnover_analysis_wrapperdata-turnover_period-period_unit-tear_sheet_filepath)
  - 6.4 Notes

## Overview

Alphalens is organized as a pipeline of five core modules:

- `alphalens.utils` prepares factor data and computes forward returns.
- `alphalens.performance` analyzes factor behavior and simulated portfolio performance.
- `alphalens.plotting` visualizes metrics and diagnostics.
- `alphalens.tears` assembles the results into tear sheets.
- `alphalens.wrapper` provides convenience wrappers for end-to-end analysis workflows.

The usual workflow is:

1. Build cleaned factor data with `alphalens.utils.get_clean_factor_and_forward_returns()`.
2. Compute diagnostics and portfolio statistics with `alphalens.performance`.
3. Visualize outputs with `alphalens.plotting`.
4. Generate presentation-ready reports with `alphalens.tears`.

All modules typically operate on a MultiIndex `pandas` object indexed by `(date, asset)`.

## alphalens.utils

Utilities for preparing factor data, computing forward returns, binning factors into quantiles/bins, and working with custom trading calendars.

This module is the main data-preparation layer used throughout Alphalens. Most workflows start with `get_clean_factor_and_forward_returns()` and then feed the resulting MultiIndex `DataFrame` into the tear sheets and plotting functions.

### Data model used by this module

Most functions operate on a `pandas` object indexed by:

- level 0: `date` / timestamp
- level 1: `asset`

Forward returns are usually stored in columns named with `pd.Timedelta`-compatible strings such as `1D`, `5D`, `30m`, or `1D1h`.

### Exceptions

##### `NonMatchingTimezoneError`

Raised when factor and pricing indices have different timezones.

##### `MaxLossExceededError`

Raised by `get_clean_factor()` when the share of dropped factor data exceeds `max_loss`.

### Core workflow

#### `compute_forward_returns(factor, prices, periods=(1, 5, 10), filter_zscore=None, cumulative_returns=True)`

Compute N-period forward returns for each asset in `factor`.

##### Input expectations

- `factor`: MultiIndex `Series` indexed by `(date, asset)`.
- `prices`: wide `DataFrame` with dates on the index and assets on the columns.
- The price history must extend far enough beyond the factor timestamps to cover the largest requested period.

##### Behavior

- Validates that factor and price timezones match.
- Infers a trading calendar when the factor index has no frequency.
- Computes forward returns for each requested period.
- Optionally filters out extreme values using `filter_zscore`.
- Names the output columns using a `Timedelta`-style string.

##### Returns

A MultiIndex `DataFrame` with the same `(date, asset)` index as the input factor.

#### `get_clean_factor(factor, forward_returns, groupby=None, binning_by_group=False, quantiles=5, bins=None, groupby_labels=None, max_loss=0.35, zero_aware=False)`

Align a factor series with already-computed forward returns and assign factor quantiles or bins.

Use this when you already have forward returns and do not need to recompute them.

##### Key behavior

- Joins factor values to forward returns.
- Optionally maps assets to groups.
- Computes factor quantiles or bins using `quantize_factor()`.
- Drops rows with missing data.
- Tracks how much data was lost and raises `MaxLossExceededError` if the loss exceeds `max_loss`.

##### Returns

A cleaned MultiIndex `DataFrame` containing forward return columns, `factor`, optionally `group`, and `factor_quantile`.

#### `get_clean_factor_and_forward_returns(factor, prices, groupby=None, binning_by_group=False, quantiles=5, bins=None, periods=(1, 5, 10), filter_zscore=20, groupby_labels=None, max_loss=0.35, zero_aware=False, cumulative_returns=True)`

One-stop helper that computes forward returns and then cleans and bins the factor data.

This is the primary entry point for most Alphalens analyses.

##### Equivalent steps

1. Call `compute_forward_returns()`
2. Call `get_clean_factor()`

##### Returns

A cleaned MultiIndex `DataFrame` suitable for Alphalens tear sheets and plots.

### Quantization and bucketing

#### `quantize_factor(factor_data, quantiles=5, bins=None, by_group=False, no_raise=False, zero_aware=False)`

Assign factor values to quantile or value bins.

##### Behavior

- Exactly one of `quantiles` or `bins` must be provided.
- Supports group-wise binning with `by_group=True`.
- Supports zero-aware binning, which splits positive and negative values separately.
- Can suppress binning failures with `no_raise=True`, returning `NaN` for problematic rows.

##### Returns

A `Series` named `factor_quantile` indexed by `(date, asset)`.

#### `non_unique_bin_edges_error(func)`

Decorator that adds a more helpful error message when `pandas` cannot create unique bin edges.

This is used internally around `quantize_factor()` to explain common binning failures, especially when many identical factor values span multiple quantiles.

### Return and performance helpers

#### `backshift_returns_series(series, N)`

Shift a MultiIndex returns series backward by `N` observations in the first level.

This helper is useful for converting backward-looking returns into forward-looking returns.

#### `demean_forward_returns(factor_data, grouper=None)`

Demean forward returns by date or by a custom grouper.

##### Behavior

- If `grouper` is not provided, demeaning happens per date.
- Only forward-return columns are adjusted.
- The result preserves the original shape and index.

#### `rate_of_return(period_ret, base_period)`

Convert returns observed over one period length into an equivalent rate for `base_period`.

This is useful for normalizing returns across different horizons.

#### `std_conversion(period_std, base_period)`

Convert standard deviation or standard error from one period length to another.

### Calendar and time utilities

#### `infer_trading_calendar(factor_idx, prices_idx)`

Infer a trading calendar from factor and price datetimes.

##### Behavior

- Detects which weekdays are traded.
- Infers holidays by comparing the observed timestamps to a weekday-specific business-day calendar.
- Returns a `CustomBusinessDay` offset.

#### `timedelta_to_string(timedelta)`

Convert a `pd.Timedelta` into a compact string compatible with `pd.Timedelta(...)`.

Example output formats include `1D`, `3h15m`, and `1D1h`.

#### `timedelta_strings_to_integers(sequence)`

Convert a sequence of timedelta strings into integer day counts.

Example: `['1D', '5D'] -> [1, 5]`.

#### `add_custom_calendar_timedelta(input, timedelta, freq)`

Add a `Timedelta` to a timestamp or `DatetimeIndex` while respecting a custom trading calendar.

##### Accepted `freq` values

- `Day`
- `BusinessDay`
- `CustomBusinessDay`

#### `make_naive_ts(t)`

Return a timezone-naive timestamp.

- If `t` is timezone-aware, it is converted to naive UTC-localized time.
- Otherwise it is localized to `None`.

#### `diff_custom_calendar_timedeltas(start, end, freq)`

Compute the effective elapsed time between two timestamps under a custom calendar.

This is used when forward-return horizons must respect trading days, weekends, and holidays.

##### Accepted `freq` values

- any `pandas.tseries.offsets.BaseOffset`
- commonly `Day`, `BusinessDay`, or `CustomBusinessDay`

### Column detection and display helpers

#### `get_forward_returns_columns(columns, require_exact_day_multiple=False)`

Identify which columns look like forward-return horizons.

##### Behavior

- Recognizes `Timedelta`-style labels such as `1D`, `5D`, `30m`, `1D1h`.
- When `require_exact_day_multiple=True`, only exact day multiples are kept.
- Emits a warning if non-day-multiple columns are skipped in that mode.

#### `print_table(table, name=None, fmt=None)`

Pretty-print a `Series` or `DataFrame`.

##### Behavior

- Uses rich display output when available.
- Falls back to standard formatted output.
- Temporarily changes `pandas` floating-point formatting when `fmt` is provided.

### Error handling helper

#### `rethrow(exception, additional_message)`

Re-raise an exception while preserving the original stack trace and appending extra context to the message.

This is used internally to make binning errors easier to diagnose.

### Practical usage

Typical Alphalens usage looks like this:

1. Prepare a factor series indexed by `(date, asset)`.
2. Prepare a price `DataFrame` with assets in columns.
3. Call `get_clean_factor_and_forward_returns()`.
4. Pass the result into tear sheets or plotting helpers.

Example call: `get_clean_factor_and_forward_returns(factor=..., prices=..., periods=(1, 5, 10))`.

### Notes

- Several functions assume data is already aligned on `(date, asset)`.
- Zero-aware binning is intended for factors centered around zero.
- `filter_zscore` can introduce lookahead bias, so use it carefully.
- Forward-return horizon labels are derived from the price calendar and may reflect custom business-day offsets.

## alphalens.performance

Performance-analysis utilities for factor research, including information coefficient calculations, factor-weighted portfolio simulation, quantile analysis, event-study helpers, and Pyfolio-ready outputs.

This module is the main analytics layer used after factor data has been cleaned and aligned with `alphalens.utils.get_clean_factor_and_forward_returns()`.

### Data model used by this module

Most functions expect a MultiIndex `pandas` object indexed by:

- level 0: `date`
- level 1: `asset`

The input usually includes:

- a `factor` column
- one or more forward-return columns such as `1D`, `5D`, or `10D`
- `factor_quantile`
- optionally `group`

Forward-return column names are detected using `alphalens.utils.get_forward_returns_columns()`.

### Core analysis functions

#### `factor_information_coefficient(factor_data, group_adjust=False, by_group=False)`

Compute the Spearman rank correlation between factor values and each forward-return horizon.

##### Behavior

- Calculates the Information Coefficient (IC) period by period.
- Optionally demeans forward returns by group before computing IC.
- Optionally computes IC separately for each group.
- Preserves the factor data frequency on the date index when not grouped by asset group.

##### Returns

A `DataFrame` of IC values indexed by date, or by date and group when `by_group=True`.

#### `mean_information_coefficient(factor_data, group_adjust=False, by_group=False, by_time=None)`

Compute the mean IC across the full sample or over a time window.

##### Behavior

- Delegates to `factor_information_coefficient()`.
- Can aggregate by time period using a pandas time rule such as monthly or weekly windows.
- Can aggregate by group when `by_group=True`.

##### Returns

A scalar-like `Series`/`DataFrame` of mean IC values depending on the requested grouping.

### Portfolio weighting and return simulation

#### `factor_weights(factor_data, demeaned=True, group_adjust=False, equal_weight=False)`

Compute asset weights from factor values.

##### Behavior

- Factor values are normalized to gross leverage of 1.
- When `demeaned=True`, weights are constructed as a long-short portfolio.
- When `group_adjust=True`, weights are computed in a group-neutral way.
- When `equal_weight=True`, assets are equal-weighted instead of factor-weighted.

##### Returns

A `Series` of weights indexed by `(date, asset)`.

#### `factor_returns(factor_data, demeaned=True, group_adjust=False, equal_weight=False, by_asset=False)`

Compute period-wise returns for a factor-weighted portfolio.

In this module, a **factor return** is the return of a simulated portfolio whose asset weights are derived from the factor signal. For each date and each forward-return horizon, the return is computed as the sum of:

$$
asset weight × asset forward return
$$

Equivalently:

$$
factor return[t, period] = Σ_i w_t,i · r_t,i,period
$$

##### Behavior

- Uses `factor_weights()` to build the portfolio.
- Multiplies weights by forward-return columns.
- If `by_asset=True`, returns the weighted return contribution of each asset.
- Otherwise, aggregates to date-level portfolio returns.

##### Worked example

Suppose one date contains three assets with these factor values and `1D` forward returns:

| asset | factor | `1D` forward return |
| --- | --- | --- |
| A | 2.0 | 0.010 |
| B | 1.0 | 0.020 |
| C | -1.0 | -0.010 |

With the default `demeaned=True`, `group_adjust=False`, and `equal_weight=False`:

1. Demean factor values by date.
   - Mean factor = $(2.0 + 1.0 - 1.0) / 3 = 0.6667$
   - Demeaned values = `A: 1.3333`, `B: 0.3333`, `C: -1.6667`
2. Normalize by the sum of absolute values.
   - Gross exposure = $|1.3333| + |0.3333| + |-1.6667| = 3.3333$
   - Weights = `A: 0.40`, `B: 0.10`, `C: -0.50`
3. Multiply each weight by the forward return.
   - `A: 0.40 $×$ 0.010 = 0.0040`
   - `B: 0.10 $×$ 0.020 = 0.0020`
   - `C: -0.50 $×$ -0.010 = 0.0050`
4. Sum across assets.
   - factor return = 0.0040 + 0.0020 + 0.0050 = 0.0110

So the factor portfolio return for that date and period is $0.011$, or 1.1%.

If `demeaned=False`, the same formula is used, but the weights come directly from the raw factor values rather than demeaned values. If `group_adjust=True`, weights are computed in a group-neutral way. If `equal_weight=True`, the code uses equal-weighted long/short buckets instead of factor-magnitude weights.

##### Returns

A `DataFrame` of period returns, or asset-level weighted returns when `by_asset=True`.

#### `factor_alpha_beta(factor_data, returns=None, demeaned=True, group_adjust=False, equal_weight=False)`

Estimate alpha and beta for a factor portfolio using OLS regression.

##### Behavior

- Uses factor portfolio returns as the dependent variable.
- Uses the universe mean return as the explanatory variable.
- If `returns` is not provided, it is computed using `factor_returns()`.
- Annualizes alpha using a 252-trading-day convention.

##### Returns

A `DataFrame` containing at least annualized alpha and beta by forward-return horizon.

#### `cumulative_returns(returns)`

Convert simple returns into cumulative returns.

This is a thin wrapper around `empyrical.cum_returns()` with a starting value of 1.

#### `positions(weights, period, freq=None)`

Build a time series of portfolio positions from factor weights.

##### Behavior

- Treats weights as active for a holding period defined by `period`.
- Uses the provided trading calendar frequency, or infers one from the weight index.
- Falls back to `BDay` and emits a warning if no frequency is available.
- Recomputes portfolio weights as positions roll forward through time.

##### Returns

A `DataFrame` with timestamps on the index and assets on the columns.

### Quantile and bucket analysis

#### `mean_return_by_quantile(factor_data, by_date=False, by_group=False, demeaned=True, group_adjust=False)`

Compute mean forward returns and standard errors by factor quantile.

##### Behavior

- Can compute results by date or across the full sample.
- Can compute results by group.
- Can demean by the whole universe or within each group.

##### Returns

A pair: $(mean_ret, std_error_ret)$.

#### `compute_mean_returns_spread(mean_returns, upper_quant, lower_quant, std_err=None)`

Compute the difference in mean returns between two quantiles.

##### Behavior

- Subtracts lower-quantile mean returns from upper-quantile mean returns.
- Optionally propagates standard error for the spread.

##### Returns

A pair: $(mean_return_difference, joint_std_err)$.

#### `quantile_turnover(quantile_factor, quantile, period=1)`

Measure the proportion of names that leave a given quantile over time.

##### Behavior

- Compares membership in the selected quantile against the prior period.
- Preserves the date frequency of the input.

##### Returns

A `Series` indexed by date.

#### `factor_rank_autocorrelation(factor_data, period=1)`

Measure the autocorrelation of factor ranks across periods.

##### Behavior

- Ranks assets by their factor values within each date, then computes the correlation between each date's rank vector and the rank vector period dates earlier.
- Useful as a turnover/stability diagnostic.

##### Returns

A `Series` of autocorrelation values indexed by date.

### Event-study helpers

#### `common_start_returns(factor, returns, before, after, cumulative=False, mean_by_date=False, demean_by=None)`

Align return windows around common event dates.

##### Behavior

- Builds a return window around each factor date and asset pair.
- Aligns all windows to a common event-time index.
- Can work with cumulative or period returns.
- Can de-mean against a reference universe.
- Can average across assets by date.

##### Returns

A `DataFrame` of aligned return windows.

#### `average_cumulative_return_by_quantile(factor_data, returns, periods_before=10, periods_after=15, demeaned=True, group_adjust=False, by_group=False)`

Compute average cumulative returns around factor events by quantile.

##### Behavior

- Uses `common_start_returns()` internally.
- Computes mean and standard deviation of event-time cumulative returns.
- Can separate results by group.
- Supports group-neutral and universe-demeaned variants.

##### Returns

A MultiIndex `DataFrame` containing mean and standard deviation across the event window.

### Portfolio simulation outputs

#### `factor_cumulative_returns(factor_data, period, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None)`

Simulate a factor portfolio and return cumulative performance.

##### Behavior

- Filters to a single forward-return horizon specified by `period`.
- Can limit analysis to selected quantiles or groups.
- Uses `factor_returns()` and then converts the result to cumulative returns.

This means cumulative factor returns are built directly from the period-wise factor return series described above.

##### Returns

A cumulative return `Series`.

#### `factor_positions(factor_data, period, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None)`

Simulate a factor portfolio and return the time series of positions.

##### Behavior

- Filters to the requested forward-return horizon.
- Reuses `factor_weights()` to compute holdings.
- Converts weights into rolling positions with `positions()`.

##### Returns

A `DataFrame` of asset positions over time.

#### `create_pyfolio_input(factor_data, period, capital=None, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None, benchmark_period="1D")`

Create returns, positions, and benchmark data in the format expected by Pyfolio.

##### Behavior

- Builds cumulative strategy returns.
- Resamples returns and positions to daily frequency.
- Adds a `cash` column to the positions output.
- Optionally converts percentage positions into dollar positions using `capital`.
- Computes a benchmark series from the factor universe when the benchmark period is available.

##### Returns

A tuple: $(returns, positions, benchmark)$.

### Dependencies and implementation notes

- Uses `pandas`, `numpy`, `scipy.stats`, `statsmodels`, and `empyrical`.
- Relies heavily on `alphalens.utils` for forward-return column detection and return demeaning.
- Most functions assume data has already been cleaned and aligned into the Alphalens MultiIndex format.
- Several functions use a trading-calendar frequency attached to the date index, so preserving index frequency is important for correct behavior.

### Practical usage

Typical workflow:

1. Build cleaned factor data with `alphalens.utils.get_clean_factor_and_forward_returns()`.
2. Compute diagnostics such as IC, mean returns by quantile, and turnover.
3. Simulate factor-weighted returns or positions.
4. Feed the outputs into plotting or Pyfolio workflows.

Example call: `factor_information_coefficient(factor_data)` or `create_pyfolio_input(factor_data, period="1D")`.

## alphalens.plotting

Visualization utilities for factor research, including plots for Information Coefficient analysis, factor returns, quantile performance, and other diagnostic charts. The module provides publication-quality visualizations with sane defaults for the Alphalens workflow.

This module visualizes the outputs from `alphalens.performance` and the cleaned factor data from `alphalens.utils`.

### Styling and context management

#### `customize(func)` --- decorator

Apply default plotting context and style to a function.

##### Behavior

- Sets seaborn colorblind-friendly palette.
- Applies default plotting context and axes style.
- Can be disabled with `set_context=False` in the decorated function call.

#### `plotting_context(context="notebook", font_scale=1.5, rc=None)`

Create an alphalens-specific plotting context.

##### Behavior

- Wraps `seaborn.plotting_context()` with alphalens defaults.
- Default line width is 1.5.
- Can be used as a context manager for multiple plots.

##### Returns

A seaborn plotting context object suitable for use in `with` statements.

#### `axes_style(style="darkgrid", rc=None)`

Create an alphalens-specific axes style context.

##### Behavior

- Wraps `seaborn.axes_style()` with alphalens defaults.
- Commonly used with `plotting_context()`.

##### Returns

A seaborn axes style object suitable for use in `with` statements.

### Data table displays

#### `plot_returns_table(alpha_beta, mean_ret_quantile, mean_ret_spread_quantile, return_df=False)`

Display a summary table of factor portfolio returns, alpha, beta, and quantile statistics.

##### Behavior

- Combines alpha/beta results with quantile return statistics.
- Converts decimal returns to basis points.
- Prints a formatted table or returns as a `DataFrame`.

##### Returns

Pretty-printed table or a `DataFrame` when `return_df=True`.

#### `plot_turnover_table(autocorrelation_data, quantile_turnover, return_df=False)`

Display quantile turnover and factor rank autocorrelation statistics.

##### Behavior

- Shows mean turnover for each quantile by period.
- Shows mean factor rank autocorrelation.
- Prints formatted tables or returns as `DataFrame`s.

##### Returns

Printed tables or a pair of `DataFrame`s when `return_df=True`.

#### `plot_information_table(ic_data, return_df=False)`

Display Information Coefficient summary statistics.

##### Behavior

- Computes IC mean, standard deviation, risk-adjusted IC, and t-statistics.
- Includes skewness and kurtosis.
- Prints a summary table or returns as a `DataFrame`.

##### Returns

Pretty-printed table or a `DataFrame` when `return_df=True`.

#### `plot_quantile_statistics_table(factor_data, return_df=False)`

Display factor value statistics by quantile.

##### Behavior

- Groups factor data by `factor_quantile`.
- Reports min, max, mean, standard deviation, and count per quantile.
- Includes count percentages.

##### Returns

Pretty-printed table or a `DataFrame` when `return_df=True`.

### Information Coefficient visualization

#### `plot_ic_ts(ic, ax=None)`

Plot the Information Coefficient time series with a rolling 22-day average.

##### Behavior

- Creates one subplot per forward-return period.
- Overlays daily IC and a 22-day moving average.
- Includes mean and standard deviation annotations.
- Aligns y-axis ranges across subplots.

##### Returns

A numpy array of matplotlib axes.

#### `plot_ic_hist(ic, ax=None)`

Plot IC as a histogram with kernel density estimate.

##### Behavior

- Creates a 3-column grid of histograms, one per forward-return period.
- Includes KDE overlay and a vertical line at the mean.
- Clamps x-axis to `[-1, 1]`.

##### Returns

A numpy array of matplotlib axes.

#### `plot_ic_qq(ic, theoretical_dist=scipy.stats.norm, ax=None)`

Plot IC values against a theoretical distribution using a Q-Q plot.

##### Behavior

- Creates a 3-column grid of Q-Q plots.
- Supports normal and Student-t distributions.
- Uses `statsmodels.qqplot()` for plotting.

##### Returns

A numpy array of matplotlib axes.

#### `plot_ic_by_group(ic_group, ax=None)`

Plot IC by group as a bar chart.

##### Behavior

- Shows mean IC for each group.
- Rotates x-axis labels for readability.

##### Returns

A matplotlib axes object.

#### `plot_monthly_ic_heatmap(mean_monthly_ic, ax=None)`

Plot IC or returns as a month/year heatmap with color coding.

##### Behavior

- Creates one heatmap per forward-return period.
- Uses reversed coolwarm colormap (red = negative, blue = positive).
- Annotates cell values.
- Centered at 0.

##### Returns

A numpy array of matplotlib axes.

### Returns analysis

#### `plot_quantile_returns_bar(mean_ret_by_q, by_group=False, ylim_percentiles=None, ax=None)`

Plot mean returns by factor quantile as a bar chart.

##### Behavior

- Optionally creates separate subplots for each group.
- Can limit y-axis range using percentiles of observed data.
- Converts to basis points.

##### Returns

A matplotlib axes object or array depending on grouping.

#### `plot_quantile_returns_violin(return_by_q, ylim_percentiles=None, ax=None)`

Plot return distributions by factor quantile using violin plots.

##### Behavior

- Shows distribution of returns within each quantile across periods.
- Uses seaborn violin plot with quartile indicators.
- Optionally limits y-axis range using percentiles.

##### Returns

A matplotlib axes object.

#### `plot_mean_quantile_returns_spread_time_series(mean_returns_spread, std_err=None, bandwidth=1, ax=None)`

Plot the top-minus-bottom quantile return spread over time.

##### Behavior

- Shows the difference between top and bottom quantile returns period by period.
- Overlays a 22-day rolling average.
- Optionally adds confidence bands based on standard error.
- Symmetrizes y-axis around zero at the 95th percentile.

##### Returns

A matplotlib axes object or array if input is a `DataFrame`.

#### `plot_cumulative_returns(factor_returns, period, freq=None, title=None, ax=None)`

Plot cumulative returns of a factor-weighted portfolio.

##### Behavior

- Converts simple returns to cumulative using `performance.cumulative_returns()`.
- Includes a reference line at 1.0 (break-even).
- Displays the forward-return period in the title.

##### Returns

A matplotlib axes object.

#### `plot_cumulative_returns_by_quantile(quantile_returns, period, freq=None, ax=None)`

Plot cumulative returns separately for each factor quantile.

##### Behavior

- Uses reversed coolwarm colormap for quantile coloring.
- Uses symmetric log scale on the y-axis for readability across wide ranges.
- Shows all quantiles on a single plot with a legend.

##### Returns

A matplotlib axes object.

#### `plot_quantile_average_cumulative_return(avg_cumulative_returns, by_quantile=False, std_bar=False, title=None, ax=None)`

Plot average cumulative returns by factor quantile around event dates.

##### Behavior

- Shows mean cumulative returns across the event window for each quantile.
- Optionally creates separate subplots per quantile for clarity.
- Can overlay standard deviation error bars.
- Uses reversed coolwarm colormap for consistency.
- Marks event date (x=0) with a vertical dashed line.

##### Returns

A matplotlib axes object or array.

### Factor characteristics

#### `plot_factor_rank_auto_correlation(factor_autocorrelation, period=1, ax=None)`

Plot factor rank autocorrelation over time.

##### Behavior

- Shows the stability of relative factor rankings.
- Includes a reference line at 0 (no autocorrelation).
- Annotates the mean autocorrelation in a text box.

##### Returns

A matplotlib axes object.

#### `plot_top_bottom_quantile_turnover(quantile_turnover, period=1, ax=None)`

Plot turnover for the top and bottom quantiles over time.

##### Behavior

- Extracts the maximum and minimum quantiles.
- Shows the proportion of names new to each quantile each period.
- Useful for detecting data quality or stationarity issues.

##### Returns

A matplotlib axes object.

#### `plot_events_distribution(events, num_bars=50, ax=None)`

Plot the distribution of factor events across time.

##### Behavior

- Divides the time span into `num_bars` intervals.
- Counts events in each interval.
- Displays as a bar chart.

##### Returns

A matplotlib axes object.

### Constants

#### `DECIMAL_TO_BPS = 10000`

Conversion factor for decimal returns to basis points. Used throughout the module when displaying returns-related plots.

### Dependencies and conventions

- **Visualization**: seaborn, matplotlib, scipy.stats
- **Analysis**: pandas, numpy, statsmodels
- **Internal**: `alphalens.utils`, `alphalens.performance`

##### Color conventions

- **Coolwarm reversed**: Red represents low/negative quantiles; blue represents high/positive quantiles.
- **Colorblind palette**: All plots use seaborn's colorblind palette for accessibility.
- **Line colors**: Green (forestgreen) for means and averages; blue (steelblue) for confidence bands; red (orangered) for rolling averages.

##### Plot conventions

- **Multi-subplot layouts**: Plots with multiple periods or groups create grid layouts (usually 1$×$3 or 2$×$2).
- **Shared axes**: Where applicable, y-axes are shared across subplots to aid comparison.
- **Reference lines**: Zero lines are included on relevant plots to indicate break-even or neutral positions.
- **Log scales**: Cumulative returns plots use symmetric log scale (`symlog`) to handle very large or very small returns.
- **Annotations**: Statistical summaries (mean, std dev) are included in text boxes on many plots.

### Practical usage

Typical workflow:

1. Compute factor diagnostics with `alphalens.performance` functions.
2. Call plotting functions with the results.
3. All plotting functions are decorated with `@customize` to apply consistent styling.
4. Optional: use `set_context=False` in any plotting call to skip automatic styling.

Example call: `plot_ic_ts(ic_data)` or `plot_quantile_returns_bar(mean_ret_by_q)`.

### Notes

- All plotting functions accept an optional `ax` parameter for custom subplot layouts.
- Return values vary: some functions print tables directly, others return `DataFrame`s or axes.
- The `return_df=False` parameter on table functions controls printing vs. returning.
- Most functions are designed for Jupyter notebooks but work in any matplotlib environment.

## alphalens.tears

Tear sheet generation for comprehensive factor analysis. A tear sheet is a multi-plot report that visualizes factor performance from multiple perspectives, including returns analysis, information coefficient statistics, turnover metrics, and event studies.

This module orchestrates the workflows of `alphalens.performance` and `alphalens.plotting` to produce production-quality analysis reports suitable for presentation and decision-making.

### Helper class

#### `GridFigure`

Utility class for managing matplotlib grid-based subplot layouts with automatic row/column navigation.

##### Methods

- `__init__(rows, cols)` --- Create a grid figure with specified dimensions.
- `next_row()` --- Get the next full-width subplot (advances to the next row).
- `next_cell()` --- Get the next cell in the current row (auto-wraps to next row when full).
- `close()` --- Close the figure and clean up resources.

##### Behavior

- Default figure size is 14 inches wide by 7 inches per row.
- Horizontal and vertical spacing are set to 0.4 and 0.3 respectively for readability.

### Tear sheet generators

All tear sheet functions are decorated with `@plotting.customize` to apply consistent styling automatically. The `set_context=False` parameter can be passed to any tear sheet to skip the decorator.

#### `create_summary_tear_sheet(factor_data, long_short=True, group_neutral=False)`

Generate a compact tear sheet with key returns, information, and turnover statistics.

##### Behavior

- Displays factor quantile statistics table.
- Computes and shows alpha, beta, top/bottom quantile returns, and spreads.
- Plots factor quantile returns bar chart.
- Computes and displays IC summary statistics.
- Analyzes turnover and factor rank autocorrelation.
- All metrics respect the `long_short` and `group_neutral` flags.

##### Returns

Displays a matplotlib figure with the complete summary.

#### `create_returns_tear_sheet(factor_data, long_short=True, group_neutral=False, by_group=False)`

Detailed tear sheet focused on returns analysis by factor quantile.

##### Behavior

- Computes factor portfolio returns.
- Displays alpha and beta metrics.
- Shows mean quantile returns as a bar chart.
- Plots return distributions using violin plots (by date across periods).
- If `'1D'` returns are available, plots cumulative portfolio returns and quantile-level cumulative returns.
- Displays top-minus-bottom quantile return spread over time with optional error bands.
- When `by_group=True`, creates separate bar charts for each asset group.

##### Parameters

- `long_short` --- Enable long-short demeaning for dollar-neutral analysis.
- `group_neutral` --- Normalize weights and returns across groups.
- `by_group` --- Create separate visualizations per group.

##### Returns

Displays one or more matplotlib figures.

#### `create_information_tear_sheet(factor_data, group_neutral=False, by_group=False)`

Tear sheet focused on Information Coefficient (IC) analysis.

##### Behavior

- Displays IC summary statistics (mean, std, risk-adjusted IC, t-stat, p-value, skewness, kurtosis).
- Plots IC time series with 22-day rolling average for each forward-return period.
- Plots IC histograms with KDE.
- Plots IC Q-Q plots against normal distribution.
- When `by_group=False` (default), creates a heatmap of monthly mean IC.
- When `by_group=True`, shows mean IC separately for each group.

##### Parameters

- `group_neutral` --- Demean forward returns by group before computing IC.
- `by_group` --- Separate analysis by asset group.

##### Returns

Displays matplotlib figure(s).

#### `create_turnover_tear_sheet(factor_data, turnover_periods=None)`

Tear sheet analyzing factor turnover and rank stability.

##### Behavior

- Displays quantile turnover statistics (mean turnover per quantile by period).
- Displays factor rank autocorrelation statistics.
- Plots time series of top and bottom quantile turnover for each period.
- Plots factor rank autocorrelation over time for each period.
- Automatically extracts day-multiple forward-return periods if `turnover_periods` is not provided.

##### Parameters

- `turnover_periods` --- Custom periods for turnover analysis. If not provided, uses exact day multiples from `factor_data`.

##### Returns

Displays matplotlib figure with turnover and autocorrelation plots.

#### `create_full_tear_sheet(factor_data, long_short=True, group_neutral=False, by_group=False)`

Comprehensive tear sheet combining all analysis perspectives.

##### Behavior

- Displays factor quantile statistics.
- Calls `create_returns_tear_sheet()` with all parameters passed through.
- Calls `create_information_tear_sheet()` with appropriate flags.
- Calls `create_turnover_tear_sheet()` with defaults.
- All component tear sheets skip automatic styling via `set_context=False` to apply consistent styling once.

##### Parameters

- `long_short` --- Enable long-short demeaning.
- `group_neutral` --- Enable group-neutral normalization.
- `by_group` --- Separate analysis per group.

##### Returns

Displays multiple matplotlib figures for all analyses.

#### `create_event_returns_tear_sheet(factor_data, returns, avgretplot=(5, 15), long_short=True, group_neutral=False, std_bar=True, by_group=False)`

Tear sheet analyzing average cumulative returns around factor events (event study).

##### Behavior

- Computes average cumulative returns within a window before and after each factor event.
- Plots overall average cumulative returns with optional error bands.
- When `std_bar=True`, plots separate cumulative return traces for each quantile with standard deviation error bars.
- When `by_group=True`, repeats the analysis separately for each asset group.
- Useful for analyzing the predictive power of a factor over different time horizons relative to the event date.

##### Parameters

- `factor_data` --- MultiIndex factor data (no forward returns required for this tear sheet).
- `returns` --- DataFrame of asset returns indexed by date.
- `avgretplot` --- Tuple of `(periods_before, periods_after)` for the event window.
- `long_short` --- Demean cumulative returns.
- `group_neutral` --- Normalize returns by group.
- `std_bar` --- Include error bar plots by quantile.
- `by_group` --- Separate analysis per group.

##### Returns

Displays matplotlib figure(s) showing event-window average returns.

#### `create_event_study_tear_sheet(factor_data, returns, avgretplot=(5, 15), rate_of_ret=True, n_bars=50)`

Tear sheet for analyzing specific events or signals.

##### Behavior

- Displays factor quantile statistics.
- Plots histogram of event distribution across time (divided into `n_bars` intervals).
- Calls `create_event_returns_tear_sheet()` internally for average cumulative returns analysis.
- Computes and displays mean quantile returns.
- Plots return distributions via violin plots by quantile.
- Can optionally annualize returns using `rate_of_ret=True`.

##### Parameters

- `factor_data` --- MultiIndex factor data indexed by event dates.
- `returns` --- Asset returns DataFrame.
- `avgretplot` --- Window for event-study cumulative returns.
- `rate_of_ret` --- Convert simple returns to annualized rates.
- `n_bars` --- Number of time intervals for event distribution histogram.

##### Returns

Displays matplotlib figures for event analysis.

### Data model

All tear sheet functions expect `factor_data` to be a MultiIndex `DataFrame` with:

- Index: `(date, asset)`
- Columns:
\beginitemize
    - Forward-return columns (e.g., `1D`, `5D`, `10D`)
    - `factor` --- The factor values
    - `factor_quantile` --- Quantile assignments
    - `group` (optional) --- Asset group identifiers

\enditemize

This is the standard output format from `alphalens.utils.get_clean_factor_and_forward_returns()`.

### Dependencies and concepts

- **Visualization**: matplotlib, seaborn
- **Analysis**: pandas, numpy, scipy.stats, statsmodels
- **Internal**: `alphalens.plotting`, `alphalens.performance`, `alphalens.utils`

##### Key tear sheet concepts

- **Long-short analysis**: Factor values are demeaned, creating equal-weight long and short sides.
- **Group-neutral analysis**: Asset groups are weighted equally, and returns are normalized within groups.
- **Quantile analysis**: Assets are divided into quantiles/buckets based on factor values; returns and metrics are computed per quantile.
- **Information Coefficient**: Spearman rank correlation between factor values and forward returns; higher IC indicates stronger predictive power.
- **Turnover**: Proportion of assets entering/leaving a quantile each period; low turnover suggests stable rankings.
- **Event study**: Analysis of returns in a window around specific factor events or signals.

### Practical usage

Typical workflow:

1. Prepare cleaned factor data with `alphalens.utils.get_clean_factor_and_forward_returns()`.
2. Call the desired tear sheet function.
3. For a quick overview, use `create_summary_tear_sheet()`.
4. For detailed analysis, use `create_full_tear_sheet()`.
5. For event-based analysis, use `create_event_returns_tear_sheet()` or `create_event_study_tear_sheet()`.

Example:

```
from alphalens.tears import create_full_tear_sheet

create_full_tear_sheet(factor_data, long_short=True, group_neutral=False)
```

### Notes

- All tear sheets automatically apply consistent styling via the `@plotting.customize` decorator.
- GridFigure handles the layout complexity automatically; most workflows don't require direct use.
- The `by_group` parameter enables side-by-side or panel analysis when asset groups are present.
- For large datasets or many forward-return periods, tear sheets can take time to render; `create_summary_tear_sheet()` is faster for quick feedback.
- All plotting occurs within the tear sheet functions; call `plt.show()` or allow the Jupyter kernel to display results automatically.

## alphalens.wrapper

High-level helpers that bundle common analysis flows and optional tear-sheet export.

### Input data expectation

Wrapper functions expect cleaned Alphalens factor data, typically from `alphalens.utils.get_clean_factor_and_forward_returns(...)`.

### Utility helpers

#### `ic_autocor_adj(daily_ic, lag=5)`

Computes lag autocorrelation, Ljung-Box p-values, and HAC/Newey-West adjusted t-stats for each IC horizon.

#### `call_with_matching_args(func, *args, **kwargs)`

Calls `func` after filtering keyword arguments to names accepted by the callable signature.

### Workflow wrappers

#### `return_analysis_wrapper(data, tear_sheet_filepath)`

Returns mean return by quantile and standard-error tables, and optionally saves a returns tear sheet.

#### `information_analysis_wrapper(data, tear_sheet_filepath)`

Computes Spearman and Pearson IC summaries (with autocorrelation-adjusted diagnostics) and optionally saves an information tear sheet.

#### `turnover_analysis_wrapper(data, turnover_period, period_unit, tear_sheet_filepath)`

Computes quantile turnover and factor-rank autocorrelation for the requested horizon and optionally saves a turnover tear sheet.

### Notes

- Wrapper functions are exposed at package level as `alphalens.wrapper`.
- The current `tests/test_wrapper.py` file is script-style and does not yet contain pytest unit tests.

