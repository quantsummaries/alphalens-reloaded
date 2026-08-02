# `alphalens.performance`

Performance-analysis utilities for factor research, including information coefficient calculations, factor-weighted portfolio simulation, quantile analysis, event-study helpers, and Pyfolio-ready outputs.

This module is the main analytics layer used after factor data has been cleaned and aligned with `alphalens.utils.get_clean_factor_and_forward_returns()`.

## Data model used by this module

Most functions expect a MultiIndex `pandas` object indexed by:

- level 0: `date`
- level 1: `asset`

The input usually includes:

- a `factor` column
- one or more forward-return columns such as `1D`, `5D`, or `10D`
- `factor_quantile`
- optionally `group`

Forward-return column names are detected using `alphalens.utils.get_forward_returns_columns()`.

## Core analysis functions

### `factor_information_coefficient(factor_data, group_adjust=False, by_group=False)`
Compute the Spearman rank correlation between factor values and each forward-return horizon.

**Behavior**

- Calculates the Information Coefficient (IC) period by period.
- Optionally demeans forward returns by group before computing IC.
- Optionally computes IC separately for each group.
- Preserves the factor data frequency on the date index when not grouped by asset group.

**Returns**

A `DataFrame` of IC values indexed by date, or by date and group when `by_group=True`.

---

### `mean_information_coefficient(factor_data, group_adjust=False, by_group=False, by_time=None)`
Compute the mean IC across the full sample or over a time window.

**Behavior**

- Delegates to `factor_information_coefficient()`.
- Can aggregate by time period using a pandas time rule such as monthly or weekly windows.
- Can aggregate by group when `by_group=True`.

**Returns**

A scalar-like `Series`/`DataFrame` of mean IC values depending on the requested grouping.

## Portfolio weighting and return simulation

### `factor_weights(factor_data, demeaned=True, group_adjust=False, equal_weight=False)`
Compute asset weights from factor values.

**Behavior**

- Factor values are normalized to gross leverage of 1.
- When `demeaned=True`, weights are constructed as a long-short portfolio.
- When `group_adjust=True`, weights are computed in a group-neutral way.
- When `equal_weight=True`, assets are equal-weighted instead of factor-weighted.

**Returns**

A `Series` of weights indexed by `(date, asset)`.

---

### `factor_returns(factor_data, demeaned=True, group_adjust=False, equal_weight=False, by_asset=False)`
Compute period-wise returns for a factor-weighted portfolio.

In this module, a **factor return** is the return of a simulated portfolio whose
asset weights are derived from the factor signal. For each date and each
forward-return horizon, the return is computed as the sum of:

`asset weight × asset forward return`

Equivalently:

`factor return[t, period] = Σ_i weight[t, i] * forward_return[t, i, period]`

**Behavior**

- Uses `factor_weights()` to build the portfolio.
- Multiplies weights by forward-return columns.
- If `by_asset=True`, returns the weighted return contribution of each asset.
- Otherwise aggregates to date-level portfolio returns.

**Worked example**

Suppose one date contains three assets with these factor values and `1D`
forward returns:

| asset | factor | `1D` forward return |
| --- | ---: | ---: |
| A | 2.0 | 0.010 |
| B | 1.0 | 0.020 |
| C | -1.0 | -0.010 |

With the default `demeaned=True`, `group_adjust=False`, and
`equal_weight=False`:

1. Demean factor values by date.
   - Mean factor = `(2.0 + 1.0 - 1.0) / 3 = 0.6667`
   - Demeaned values = `A: 1.3333`, `B: 0.3333`, `C: -1.6667`
2. Normalize by the sum of absolute values.
   - Gross exposure = `|1.3333| + |0.3333| + |−1.6667| = 3.3333`
   - Weights = `A: 0.40`, `B: 0.10`, `C: -0.50`
3. Multiply each weight by the forward return.
   - `A: 0.40 × 0.010 = 0.0040`
   - `B: 0.10 × 0.020 = 0.0020`
   - `C: -0.50 × -0.010 = 0.0050`
4. Sum across assets.
   - `factor return = 0.0040 + 0.0020 + 0.0050 = 0.0110`

So the factor portfolio return for that date and period is `0.011`, or `1.1%`.

If `demeaned=False`, the same formula is used, but the weights come directly
from the raw factor values rather than demeaned values. If `group_adjust=True`,
weights are computed in a group-neutral way. If `equal_weight=True`, the code
uses equal-weighted long/short buckets instead of factor-magnitude weights.

**Returns**

A `DataFrame` of period returns, or asset-level weighted returns when `by_asset=True`.

---

### `factor_alpha_beta(factor_data, returns=None, demeaned=True, group_adjust=False, equal_weight=False)`
Estimate alpha and beta for a factor portfolio using OLS regression.

**Behavior**

- Uses factor portfolio returns as the dependent variable.
- Uses the universe mean return as the explanatory variable.
- If `returns` is not provided, it is computed using `factor_returns()`.
- Annualizes alpha using a 252-trading-day convention.

**Returns**

A `DataFrame` containing at least annualized alpha and beta by forward-return horizon.

---

### `cumulative_returns(returns)`
Convert simple returns into cumulative returns.

This is a thin wrapper around `empyrical.cum_returns()` with a starting value of 1.

---

### `positions(weights, period, freq=None)`
Build a time series of portfolio positions from factor weights.

**Behavior**

- Treats weights as active for a holding period defined by `period`.
- Uses the provided trading calendar frequency, or infers one from the weight index.
- Falls back to `BDay` and emits a warning if no frequency is available.
- Recomputes portfolio weights as positions roll forward through time.

**Returns**

A `DataFrame` with timestamps on the index and assets on the columns.

## Quantile and bucket analysis

### `mean_return_by_quantile(factor_data, by_date=False, by_group=False, demeaned=True, group_adjust=False)`
Compute mean forward returns and standard errors by factor quantile.

**Behavior**

- Can compute results by date or across the full sample.
- Can compute results by group.
- Can demean by the whole universe or within each group.

**Returns**

A pair: `(mean_ret, std_error_ret)`.

---

### `compute_mean_returns_spread(mean_returns, upper_quant, lower_quant, std_err=None)`
Compute the difference in mean returns between two quantiles.

**Behavior**

- Subtracts lower-quantile mean returns from upper-quantile mean returns.
- Optionally propagates standard error for the spread.

**Returns**

A pair: `(mean_return_difference, joint_std_err)`.

---

### `quantile_turnover(quantile_factor, quantile, period=1)`
Measure the proportion of names that leave a given quantile over time.

**Behavior**

- Compares membership in the selected quantile against the prior period.
- Preserves the date frequency of the input.

**Returns**

A `Series` indexed by date.

---

### `factor_rank_autocorrelation(factor_data, period=1)`
Measure the autocorrelation of factor ranks across periods.

**Behavior**

- Ranks factor values by date before computing autocorrelation.
- Useful as a turnover/stability diagnostic.

**Returns**

A `Series` of autocorrelation values indexed by date.

## Event-study helpers

### `common_start_returns(factor, returns, before, after, cumulative=False, mean_by_date=False, demean_by=None)`
Align return windows around common event dates.

**Behavior**

- Builds a return window around each factor date and asset pair.
- Aligns all windows to a common event-time index.
- Can work with cumulative or period returns.
- Can de-mean against a reference universe.
- Can average across assets by date.

**Returns**

A `DataFrame` of aligned return windows.

---

### `average_cumulative_return_by_quantile(factor_data, returns, periods_before=10, periods_after=15, demeaned=True, group_adjust=False, by_group=False)`
Compute average cumulative returns around factor events by quantile.

**Behavior**

- Uses `common_start_returns()` internally.
- Computes mean and standard deviation of event-time cumulative returns.
- Can separate results by group.
- Supports group-neutral and universe-demeaned variants.

**Returns**

A MultiIndex `DataFrame` containing mean and standard deviation across the event window.

## Portfolio simulation outputs

### `factor_cumulative_returns(factor_data, period, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None)`
Simulate a factor portfolio and return cumulative performance.

**Behavior**

- Filters to a single forward-return horizon specified by `period`.
- Can limit analysis to selected quantiles or groups.
- Uses `factor_returns()` and then converts the result to cumulative returns.

This means cumulative factor returns are built directly from the period-wise
factor return series described above.

**Returns**

A cumulative return `Series`.

---

### `factor_positions(factor_data, period, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None)`
Simulate a factor portfolio and return the time series of positions.

**Behavior**

- Filters to the requested forward-return horizon.
- Reuses `factor_weights()` to compute holdings.
- Converts weights into rolling positions with `positions()`.

**Returns**

A `DataFrame` of asset positions over time.

---

### `create_pyfolio_input(factor_data, period, capital=None, long_short=True, group_neutral=False, equal_weight=False, quantiles=None, groups=None, benchmark_period="1D")`
Create returns, positions, and benchmark data in the format expected by Pyfolio.

**Behavior**

- Builds cumulative strategy returns.
- Resamples returns and positions to daily frequency.
- Adds a `cash` column to the positions output.
- Optionally converts percentage positions into dollar positions using `capital`.
- Computes a benchmark series from the factor universe when the benchmark period is available.

**Returns**

A tuple: `(returns, positions, benchmark)`.

## Dependencies and implementation notes

- Uses `pandas`, `numpy`, `scipy.stats`, `statsmodels`, and `empyrical`.
- Relies heavily on `alphalens.utils` for forward-return column detection and return demeaning.
- Most functions assume data has already been cleaned and aligned into the Alphalens MultiIndex format.
- Several functions use a trading-calendar frequency attached to the date index, so preserving index frequency is important for correct behavior.

## Practical usage

Typical workflow:

1. Build cleaned factor data with `alphalens.utils.get_clean_factor_and_forward_returns()`.
2. Compute diagnostics such as IC, mean returns by quantile, and turnover.
3. Simulate factor-weighted returns or positions.
4. Feed the outputs into plotting or Pyfolio workflows.

Example call: `factor_information_coefficient(factor_data)` or `create_pyfolio_input(factor_data, period="1D")`.

