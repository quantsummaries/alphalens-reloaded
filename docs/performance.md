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

### `factor_information_coefficient(factor_data, group_adjust=False, by_group=False, ic_type="spearman")`
Compute the Information Coefficient (IC) between factor values and each forward-return horizon.

**Behavior**

- Calculates IC period by period using either:
  - Spearman rank correlation (`ic_type="spearman"`, default), or
  - Pearson linear correlation (`ic_type="pearson"`).
- Optionally demeans forward returns by group before computing IC.
- Optionally computes IC separately for each group.
- Preserves the factor data frequency on the date index when not grouped by asset group.
- Raises `ValueError` for unsupported `ic_type` values.

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

**Worked example**

Suppose one date contains three assets with these factor values:

| asset | factor |
| --- | ---: |
| A | 2.0 |
| B | 1.0 |
| C | -1.0 |

With the default `demeaned=True`, `group_adjust=False`, and
`equal_weight=False`:

1. Demean factor values by date.
   - Mean factor = `(2.0 + 1.0 - 1.0) / 3 = 0.6667`
   - Demeaned values = `A: 1.3333`, `B: 0.3333`, `C: -1.6667`
2. Normalize by the sum of absolute values.
   - Gross exposure = `|1.3333| + |0.3333| + |−1.6667| = 3.3333`
   - Weights = `A: 0.40`, `B: 0.10`, `C: -0.50`

These weights represent a dollar-neutral long-short portfolio: long positions
(`A: 0.40`, `B: 0.10`) total `0.50` and short positions (`C: -0.50`) total
`0.50` in absolute value.

If `demeaned=False`, weights come directly from the raw (non-demeaned) factor
values: the sum of absolute raw factors would be `|2.0| + |1.0| + |−1.0| = 4.0`,
yielding weights `A: 0.50`, `B: 0.25`, `C: -0.25`. If `group_adjust=True`,
weights are adjusted to be group-neutral. If `equal_weight=True`, assets are
equal-weighted within long and short buckets instead of using factor magnitudes.

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
- Otherwise, aggregates to date-level portfolio returns.

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

### `factor_alpha_beta(factor_data: pd.DataFrame, returns: Optional[Union[pd.DataFrame, pd.Series]]=None, demeaned: bool=True, group_adjust: bool=False, equal_weight: bool=False) -> pd.DataFrame`
Estimate alpha and beta for a factor portfolio using OLS regression.

**Behavior**

- Uses factor portfolio returns as the dependent variable.
- Uses the universe mean return as the explanatory variable.
- If `returns` is not provided, it is computed using `factor_returns()`.
- Annualizes alpha using a 252-trading-day convention.

**Returns**

A `DataFrame` containing at least annualized alpha and beta by forward-return horizon.

**How alpha and beta are calculated**

For each forward-return horizon (for example `1D`, `5D`), the function runs:

`r_factor[t] = alpha + beta * r_universe[t] + eps[t]`

- `r_factor[t]`: factor portfolio return from `factor_returns()`.
- `r_universe[t]`: cross-sectional mean universe return for the same horizon.
- `beta`: OLS slope (sensitivity to universe return).
- `alpha`: OLS intercept, then annualized as
  `(1 + alpha) ** (Timedelta("252Days") / Timedelta(period)) - 1`.

The output currently stores rows labeled `Ann. alpha` and `beta` per horizon.

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

**Index shape by (`by_date`, `by_group`)**

For both outputs (`mean_ret` and `std_error_ret`), columns are forward-return horizons (for example `1D`, `5D`, `10D`).

- `by_date=True`, `by_group=False` -> index is `(factor_quantile, date)`.
- `by_date=True`, `by_group=True` -> index is `(factor_quantile, date, group)`.
- `by_date=False`, `by_group=False` -> index is `(factor_quantile)`.
- `by_date=False`, `by_group=True` -> index is `(factor_quantile, group)`.

When `by_date=False`, the function first computes date-level statistics and then averages over the date level.

**Numerical illustration**

Assume `by_date=False`, `by_group=False`, and one horizon (`1D`).

- Date-level quantile means after the first aggregation step:
  - Q1: `[-0.010, -0.006]`
  - Q5: `[0.012, 0.008]`
- Final mean by quantile (second aggregation across dates):
  - Q1 mean: `(-0.010 + -0.006) / 2 = -0.008`
  - Q5 mean: `(0.012 + 0.008) / 2 = 0.010`
- Standard error uses `std / sqrt(count)` on those date-level means:
  - For both Q1 and Q5, sample std is about `0.002828` and `count=2`, so
    `std_error_ret ~= 0.002828 / sqrt(2) = 0.002`.

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

**Worked example**

Suppose we evaluate `quantile=5` with `period=1`, and the names in quantile 5 are:

| date | names in quantile 5 |
| --- | --- |
| 2026-01-02 | `{A, B, C}` |
| 2026-01-03 | `{B, C, D}` |
| 2026-01-06 | `{C, D, E}` |

For each date after the first, turnover is:

`(# names that are new vs previous date) / (current quantile size)`

- On `2026-01-03`, new names vs `2026-01-02` are `{D}`.
  - Turnover = `1 / 3 = 0.3333`
- On `2026-01-06`, new names vs `2026-01-03` are `{E}`.
  - Turnover = `1 / 3 = 0.3333`

The first date has no prior comparison point, so no turnover value is reported for it.

**Companion example (`period=2`)**

Using the same memberships, each date is compared to the set two dates earlier.

- On `2026-01-06`, compare `{C, D, E}` to `2026-01-02` (`{A, B, C}`).
  - New names are `{D, E}`.
  - Turnover = `2 / 3 = 0.6667`

This highlights that larger `period` values measure non-adjacent membership change.
If intermediate dates are missing after frequency alignment (for example via `asfreq`), larger `period` comparisons can be skipped or shifted to different comparable dates.

**Returns**

A `Series` indexed by date.

---

### `factor_rank_autocorrelation(factor_data, period=1)`
Measure the autocorrelation of factor ranks across periods.

**Behavior**

- Ranks assets by their factor values within each date, then computes the correlation between each date’s rank vector and the rank vector period dates earlier.
- Useful as a turnover/stability diagnostic.

**Worked example (`period=1`)**

Suppose the factor values for assets `A, B, C, D` are:

| date | factor values (A, B, C, D) | rank vector (A, B, C, D) |
| --- | --- | --- |
| 2026-01-02 | `(1, 2, 3, 4)` | `(1, 2, 3, 4)` |
| 2026-01-03 | `(4, 3, 2, 1)` | `(4, 3, 2, 1)` |
| 2026-01-06 | `(1, 2, 3, 4)` | `(1, 2, 3, 4)` |

With `period=1`, each date is correlated with the immediately prior date:

- On `2026-01-03`: corr(`(4, 3, 2, 1)`, `(1, 2, 3, 4)`) = `-1.0`
- On `2026-01-06`: corr(`(1, 2, 3, 4)`, `(4, 3, 2, 1)`) = `-1.0`

The first date has no prior rank vector, so its value is `NaN`.

**Companion example (`period=2`)**

Using the same data with `period=2`, `2026-01-06` is compared to `2026-01-02`:

- corr(`(1, 2, 3, 4)`, `(1, 2, 3, 4)`) = `1.0`

So a larger `period` can reveal longer-horizon rank stability even when adjacent dates are unstable.

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

## Per-function dependency table

| Function | Purpose | Direct deps in `performance.py` | Direct deps in `utils` | Direct external deps |
| --- | --- | --- | --- | --- |
| `factor_information_coefficient` | Compute date-wise IC (Spearman/Pearson) between factor and forward returns. | - | `get_forward_returns_columns`, `demean_forward_returns` | `stats.spearmanr`, `stats.pearsonr` |
| `mean_information_coefficient` | Aggregate IC means by time and/or group. | `factor_information_coefficient` | - | `pd.Grouper` |
| `factor_weights` | Build normalized factor-based asset weights (optional demean/group adjust/equal-weight). | - | - | - |
| `factor_returns` | Compute factor-weighted forward returns per period. | `factor_weights` | `get_forward_returns_columns` | - |
| `factor_alpha_beta` | Regress factor returns on universe mean returns to estimate alpha/beta. | `factor_returns` | `get_forward_returns_columns` | `add_constant`, `OLS` |
| `cumulative_returns` | Convert simple returns series to cumulative returns. | - | - | `ep.cum_returns` |
| `positions` | Build position time series from weights and holding periods. | - | `add_custom_calendar_timedelta` | `BDay`, `warnings.warn` |
| `mean_return_by_quantile` | Compute mean/std-error of forward returns by quantile/date/group. | - | `demean_forward_returns`, `get_forward_returns_columns` | `np.sqrt` |
| `compute_mean_returns_spread` | Compute spread between upper and lower quantile mean returns. | - | - | `np.sqrt` |
| `quantile_turnover` | Measure membership turnover for a quantile over a lag period. | - | - | `pd.isna` |
| `factor_rank_autocorrelation` | Compute autocorrelation of mean factor rank across dates. | - | - | - |
| `common_start_returns` | Align returns around event dates into common-relative windows. | `cumulative_returns` | - | - |
| `average_cumulative_return_by_quantile` | Compute average cumulative event returns by quantile (optionally by group). | `common_start_returns` | - | `np.inf` |
| `factor_cumulative_returns` | Simulate portfolio and return cumulative returns for a chosen period. | `factor_returns`, `cumulative_returns` | `get_forward_returns_columns` | - |
| `factor_positions` | Simulate portfolio and return position matrix over time. | `factor_weights`, `positions` | `get_forward_returns_columns` | - |
| `create_pyfolio_input` | Build returns/positions/benchmark outputs formatted for Pyfolio. | `factor_cumulative_returns`, `factor_positions` | `get_forward_returns_columns` | - |

## Practical usage

Typical workflow:

1. Build cleaned factor data with `alphalens.utils.get_clean_factor_and_forward_returns()`.
2. Compute diagnostics such as IC, mean returns by quantile, and turnover.
3. Simulate factor-weighted returns or positions.
4. Feed the outputs into plotting or Pyfolio workflows.

Example call: `factor_information_coefficient(factor_data)` or `create_pyfolio_input(factor_data, period="1D")`.

