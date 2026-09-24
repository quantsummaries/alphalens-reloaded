# `alphalens.utils`

Utilities for preparing factor data, computing forward returns, binning factors into quantiles/bins, and working with custom trading calendars.

This module is the main data-preparation layer used throughout Alphalens. Most workflows start with `get_clean_factor_and_forward_returns()` and then feed the resulting MultiIndex DataFrame into the tear sheets and plotting functions.

## Data model used by this module

Most functions operate on a `pandas` object indexed by:

- level 0: `date` / timestamp
- level 1: `asset`

Forward returns are usually stored in columns named with `pd.Timedelta`-compatible strings such as `1D`, `5D`, `30m`, or `1D1h`.

## Exceptions

### `NonMatchingTimezoneError`
Raised when factor and pricing indices have different timezones.

### `MaxLossExceededError`
Raised by `get_clean_factor()` when the share of dropped factor data exceeds `max_loss`.

## Core workflow

### `compute_forward_returns(factor: pd.Series, prices: pd.DataFrame, periods: Sequence[int]=(1, 5, 10), filter_zscore: Optional[float]=None, cumulative_returns=True) -> pd.DataFrame`
Compute N-period forward returns for each asset in `factor`.

**Input expectations**

- `factor`: MultiIndex `Series` indexed by `(date, asset)`.
- `prices`: wide `DataFrame` with dates on the index and assets on the columns.
- The price history must extend far enough beyond the factor timestamps to cover the largest requested period.

**Behavior**

- Validates that factor and price timezones match.
- Infers a trading calendar when the factor index has no frequency.
- Computes forward returns for each requested period.
- Optionally filters out extreme values using `filter_zscore`.
- Names the output columns using a `Timedelta`-style string.

**Returns**

A MultiIndex `DataFrame` with the same `(date, asset)` index as the input factor.

---

### `get_clean_factor(factor: pd.Series, forward_returns: pd.DataFrame, groupby: Optional[Union[pd.Series, dict[Any, Any]]] = None, binning_by_group: bool = False, quantiles: Optional[Union[int, Sequence[float]]] = 5, bins: Optional[Union[int, Sequence[float]]] = None, groupby_labels: Optional[dict[Any, Any]] = None, max_loss: float = 0.35, zero_aware: bool = False) -> pd.DataFrame`
Align a factor series with already-computed forward returns and assign factor quantiles or bins.

Use this when you already have forward returns and do not need to recompute them.

**Key behavior**

- Joins factor values to forward returns.
- Optionally maps assets to groups.
- Computes factor quantiles or bins using `quantize_factor()`.
- Drops rows with missing data.
- Tracks how much data was lost and raises `MaxLossExceededError` if the loss exceeds `max_loss`.

**Returns**

A cleaned MultiIndex `DataFrame` containing:

- forward return columns
- `factor`
- optionally `group`
- `factor_quantile`

---

### `get_clean_factor_and_forward_returns(factor: pd.Series, prices: pd.DataFrame, groupby: Optional[Union[pd.Series, dict[Any, Any]]] = None, binning_by_group: bool = False, quantiles: Optional[Union[int, Sequence[float]]] = 5, bins: Optional[Union[int, Sequence[float]]] = None, periods: Sequence[int] = (1, 5, 10), filter_zscore: Optional[float] = 20, groupby_labels: Optional[dict[Any, Any]] = None, max_loss: float = 0.35, zero_aware: bool = False, cumulative_returns: bool = True) -> pd.DataFrame`
One-stop helper that computes forward returns and then cleans and bins the factor data.

This is the primary entry point for most Alphalens analyses.

**Equivalent steps**

1. Call `compute_forward_returns()`
2. Call `get_clean_factor()`

**Returns**

A cleaned MultiIndex `DataFrame` suitable for Alphalens tear sheets and plots.

## Quantization and bucketing

### `quantize_factor(factor_data: pd.DataFrame, quantiles: Optional[Union[int, Sequence[float]]] = 5, bins: Optional[Union[int, Sequence[float]]] = None, by_group: bool = False, no_raise: bool = False, zero_aware: bool = False) -> pd.Series`
Assign factor values to quantile or value bins.

**Behavior**

- Exactly one of `quantiles` or `bins` must be provided.
- Supports group-wise binning with `by_group=True`.
- Supports zero-aware binning, which splits positive and negative values separately.
- Can suppress binning failures with `no_raise=True`, returning `NaN` for problematic rows.

**Returns**

A `Series` named `factor_quantile` indexed by `(date, asset)`.

---

### `non_unique_bin_edges_error(func)`
Decorator that adds a more helpful error message when `pandas` cannot create unique bin edges.

This is used internally around `quantize_factor()` to explain common binning failures, especially when many identical factor values span multiple quantiles.

## Return and performance helpers

### `backshift_returns_series(series, N)`
Shift a MultiIndex returns series backward by `N` observations in the first level.

This helper is useful for converting backward-looking returns into forward-looking returns.

---

### `demean_forward_returns(factor_data, grouper=None)`
Demean forward returns by date or by a custom grouper.

**Behavior**

- If `grouper` is not provided, demeaning happens per date.
- Only forward-return columns are adjusted.
- The result preserves the original shape and index.

---

### `rate_of_return(period_ret, base_period)`
Convert returns observed over one period length into an equivalent rate for `base_period`.

This is useful for normalizing returns across different horizons.

---

### `std_conversion(period_std, base_period)`
Convert standard deviation or standard error from one period length to another.

---

## Calendar and time utilities

### `infer_trading_calendar(factor_idx, prices_idx)`
Infer a trading calendar from factor and price datetimes.

**Behavior**

- Detects which weekdays are traded.
- Infers holidays by comparing the observed timestamps to a weekday-specific business-day calendar.
- Returns a `CustomBusinessDay` offset.

---

### `timedelta_to_string(timedelta)`
Convert a `pd.Timedelta` into a compact string compatible with `pd.Timedelta(...)`.

Example output formats include `1D`, `3h15m`, and `1D1h`.

---

### `timedelta_strings_to_integers(sequence)`
Convert a sequence of timedelta strings into integer day counts.

Example: `['1D', '5D'] -> [1, 5]`.

---

### `add_custom_calendar_timedelta(input, timedelta, freq)`
Add a `Timedelta` to a timestamp or `DatetimeIndex` while respecting a custom trading calendar.

**Accepted `freq` values**

- `Day`
- `BusinessDay`
- `CustomBusinessDay`

---

### `make_naive_ts(t)`
Return a timezone-naive timestamp.

- If `t` is timezone-aware, it is converted to naive UTC-localized time.
- Otherwise it is localized to `None`.

---

### `diff_custom_calendar_timedeltas(start, end, freq)`
Compute the effective elapsed time between two timestamps under a custom calendar.

This is used when forward-return horizons must respect trading days, weekends, and holidays.

**Accepted `freq` values**

- any `pandas.tseries.offsets.BaseOffset`
- commonly `Day`, `BusinessDay`, or `CustomBusinessDay`

## Column detection and display helpers

### `get_forward_returns_columns(columns: pd.Index, require_exact_day_multiple=False) -> pd.Index`
Identify which columns look like forward-return horizons.

**Behavior**

- Recognizes `Timedelta`-style labels such as `1D`, `5D`, `30m`, `1D1h`.
- When `require_exact_day_multiple=True`, only exact day multiples are kept.
- Emits a warning if non-day-multiple columns are skipped in that mode.
- Expects `columns` to be a `pandas.Index` and returns a filtered `pandas.Index`.

---

### `print_table(table, name=None, fmt=None)`
Pretty-print a `Series` or `DataFrame`.

**Behavior**

- Uses rich display output when available.
- Falls back to standard formatted output.
- Temporarily changes `pandas` floating-point formatting when `fmt` is provided.

## Error handling helper

### `rethrow(exception, additional_message)`
Re-raise an exception while preserving the original stack trace and appending extra context to the message.

This is used internally to make binning errors easier to diagnose.

## Per-function dependency table

This table lists direct dependencies only (not transitive call chains).

| Function | Purpose | Direct deps in `utils.py` | Direct external deps |
| --- | --- | --- | --- |
| `rethrow` | Re-raise an exception with an appended message while preserving traceback. | - | - |
| `non_unique_bin_edges_error` | Decorator that rewrites non-unique-bin-edge errors with clearer guidance. | `rethrow` | - |
| `quantize_factor` | Assign factor values to quantile/bin buckets by date (optionally by group/zero-aware). | `non_unique_bin_edges_error` (decorator) | `pd.qcut`, `pd.cut`, `pd.concat`, `pd.Series` |
| `infer_trading_calendar` | Infer a trading calendar (`CustomBusinessDay`) from factor and price indices. | - | `pd.date_range`, `CustomBusinessDay` |
| `compute_forward_returns` | Compute forward returns aligned to factor timestamps and infer/keep trading frequency. | `infer_trading_calendar`, `diff_custom_calendar_timedeltas`, `timedelta_to_string` | `pd.MultiIndex.from_product`, `pd.Timedelta`, `np.concatenate`, `np.nan`, `mode` |
| `backshift_returns_series` | Shift a MultiIndex returns series backward by `N` observations on date level. | - | `pd.MultiIndex`, `pd.Series`, `np.array` |
| `demean_forward_returns` | Demean forward returns by date or by provided groupers. | `get_forward_returns_columns` | - |
| `print_table` | Pretty-print a `Series`/`DataFrame` with optional temporary float formatting. | - | `pd.DataFrame`, `pd.Series`, `pd.get_option`, `pd.set_option`, `display` |
| `get_clean_factor` | Merge factor, forward returns, and group labels; then bin and enforce max-loss checks. | `quantize_factor` | `pd.Series`, `np.isfinite` |
| `get_clean_factor_and_forward_returns` | End-to-end helper to compute forward returns and return clean factor data. | `compute_forward_returns`, `get_clean_factor` | - |
| `rate_of_return` | Convert period return to an equivalent rate for a base period. | - | `pd.Timedelta` |
| `std_conversion` | Scale period std/std-error to an equivalent base-period value. | - | `pd.Timedelta`, `np.sqrt` |
| `get_forward_returns_columns` | Detect columns that match forward-return horizon naming conventions. | - | `re.compile`, `warnings.warn` |
| `timedelta_to_string` | Convert a `Timedelta` to the string format used in forward-return column names. | - | - |
| `timedelta_strings_to_integers` | Convert timedelta strings like `['1D', '5D']` to integer day counts. | - | `pd.Timedelta` |
| `add_custom_calendar_timedelta` | Add a `Timedelta` using a trading-calendar-aware offset. | - | `pd.Timedelta`, `Day`, `BusinessDay`, `CustomBusinessDay` |
| `make_naive_ts` | Convert a timestamp to timezone-naive form. | - | pandas timestamp tz methods |
| `diff_custom_calendar_timedeltas` | Compute elapsed `Timedelta` under a custom/business-day calendar. | `make_naive_ts` | `np.busday_count`, `pd.date_range`, `pd.Timedelta`, `BaseOffset`, `Day`, `BusinessDay` |
| `ic_autocor_adj` | Compute IC autocorrelation diagnostics and Newey-West-adjusted t-stats. | - | `acorr_ljungbox`, `sm.add_constant`, `sm.OLS`, `np.ones`, `pd.DataFrame` |

## Practical usage

Typical Alphalens usage looks like this:

1. Prepare a factor series indexed by `(date, asset)`.
2. Prepare a price DataFrame with assets in columns.
3. Call `get_clean_factor_and_forward_returns()`.
4. Pass the result into tear sheets or plotting helpers.

The same cleaned output is also the required input for the new high-level wrappers in `alphalens.wrapper` (`return_analysis_wrapper`, `information_analysis_wrapper`, and `turnover_analysis_wrapper`).

Example call: `get_clean_factor_and_forward_returns(factor=..., prices=..., periods=(1, 5, 10))`.

## Notes

- Several functions assume data is already aligned on `(date, asset)`.
- Zero-aware binning is intended for factors centered around zero.
- `filter_zscore` can introduce lookahead bias, so use it carefully.
- Forward-return horizon labels are derived from the price calendar and may reflect custom business-day offsets.


