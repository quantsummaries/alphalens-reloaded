# `alphalens.tears`

Tear sheet generation for comprehensive factor analysis. A tear sheet is a multi-plot report that visualizes factor performance from multiple perspectives, including returns analysis, information coefficient statistics, turnover metrics, and event studies.

This module orchestrates the workflows of `alphalens.performance` and `alphalens.plotting` to produce production-quality analysis reports suitable for presentation and decision-making.

## Helper class

### `GridFigure`
Utility class for managing matplotlib grid-based subplot layouts with automatic row/column navigation.

**Methods**

- `__init__(rows, cols)` — Create a grid figure with specified dimensions.
- `next_row()` — Get the next full-width subplot (advances to the next row).
- `next_cell()` — Get the next cell in the current row (auto-wraps to next row when full).
- `close()` — Close the figure and clean up resources.

**Behavior**

- Default figure size is 14 inches wide by 7 inches per row.
- Horizontal and vertical spacing are set to 0.4 and 0.3 respectively for readability.

---

## Tear sheet generators

All tear sheet functions are decorated with `@plotting.customize` to apply consistent styling automatically. The `set_context=False` parameter can be passed to any tear sheet to skip the decorator.

### `create_summary_tear_sheet(factor_data, long_short=True, group_neutral=False)`
Generate a compact tear sheet with key returns, information, and turnover statistics.

**Behavior**

- Displays factor quantile statistics table.
- Computes and shows alpha, beta, top/bottom quantile returns, and spreads.
- Plots factor quantile returns bar chart.
- Computes and displays IC summary statistics.
- Analyzes turnover and factor rank autocorrelation.
- All metrics respect the `long_short` and `group_neutral` flags.

**Returns**

Displays a matplotlib figure with the complete summary.

---

### `create_returns_tear_sheet(factor_data, long_short=True, group_neutral=False, by_group=False)`
Detailed tear sheet focused on returns analysis by factor quantile.

**Behavior**

- Computes factor portfolio returns.
- Displays alpha and beta metrics.
- Shows mean quantile returns as a bar chart.
- Plots return distributions using violin plots (by date across periods).
- If '1D' returns are available, plots cumulative portfolio returns and quantile-level cumulative returns.
- Displays top-minus-bottom quantile return spread over time with optional error bands.
- When `by_group=True`, creates separate bar charts for each asset group.

**Parameters**

- `long_short` — Enable long-short demeaning for dollar-neutral analysis.
- `group_neutral` — Normalize weights and returns across groups.
- `by_group` — Create separate visualizations per group.

**Returns**

Displays one or more matplotlib figures.

---

### `create_information_tear_sheet(factor_data, group_neutral=False, by_group=False)`
Tear sheet focused on Information Coefficient (IC) analysis.

**Behavior**

- Displays IC summary statistics (mean, std, risk-adjusted IC, t-stat, p-value, skewness, kurtosis).
- Plots IC time series with 22-day rolling average for each forward-return period.
- Plots IC histograms with KDE.
- Plots IC Q-Q plots against normal distribution.
- When `by_group=False` (default), creates a heatmap of monthly mean IC.
- When `by_group=True`, shows mean IC separately for each group.

**Parameters**

- `group_neutral` — Demean forward returns by group before computing IC.
- `by_group` — Separate analysis by asset group.

**Returns**

Displays matplotlib figure(s).

---

### `create_turnover_tear_sheet(factor_data, turnover_periods=None)`
Tear sheet analyzing factor turnover and rank stability.

**Behavior**

- Displays quantile turnover statistics (mean turnover per quantile by period).
- Displays factor rank autocorrelation statistics.
- Plots time series of top and bottom quantile turnover for each period.
- Plots factor rank autocorrelation over time for each period.
- Automatically extracts day-multiple forward-return periods if `turnover_periods` is not provided.

**Parameters**

- `turnover_periods` — Custom periods for turnover analysis. If not provided, uses exact day multiples from `factor_data`.

**Returns**

Displays matplotlib figure with turnover and autocorrelation plots.

---

### `create_full_tear_sheet(factor_data, long_short=True, group_neutral=False, by_group=False)`
Comprehensive tear sheet combining all analysis perspectives.

**Behavior**

- Displays factor quantile statistics.
- Calls `create_returns_tear_sheet()` with all parameters passed through.
- Calls `create_information_tear_sheet()` with appropriate flags.
- Calls `create_turnover_tear_sheet()` with defaults.
- All component tear sheets skip automatic styling via `set_context=False` to apply consistent styling once.

**Parameters**

- `long_short` — Enable long-short demeaning.
- `group_neutral` — Enable group-neutral normalization.
- `by_group` — Separate analysis per group.

**Returns**

Displays multiple matplotlib figures for all analyses.

---

### `create_event_returns_tear_sheet(factor_data, returns, avgretplot=(5, 15), long_short=True, group_neutral=False, std_bar=True, by_group=False)`
Tear sheet analyzing average cumulative returns around factor events (event study).

**Behavior**

- Computes average cumulative returns within a window before and after each factor event.
- Plots overall average cumulative returns with optional error bands.
- When `std_bar=True`, plots separate cumulative return traces for each quantile with standard deviation error bars.
- When `by_group=True`, repeats the analysis separately for each asset group.
- Useful for analyzing the predictive power of a factor over different time horizons relative to the event date.

**Parameters**

- `factor_data` — MultiIndex factor data (no forward returns required for this tear sheet).
- `returns` — DataFrame of asset returns indexed by date.
- `avgretplot` — Tuple of `(periods_before, periods_after)` for the event window.
- `long_short` — Demean cumulative returns.
- `group_neutral` — Normalize returns by group.
- `std_bar` — Include error bar plots by quantile.
- `by_group` — Separate analysis per group.

**Returns**

Displays matplotlib figure(s) showing event-window average returns.

---

### `create_event_study_tear_sheet(factor_data, returns, avgretplot=(5, 15), rate_of_ret=True, n_bars=50)`
Tear sheet for analyzing specific events or signals.

**Behavior**

- Displays factor quantile statistics.
- Plots histogram of event distribution across time (divided into `n_bars` intervals).
- Calls `create_event_returns_tear_sheet()` internally for average cumulative returns analysis.
- Computes and displays mean quantile returns.
- Plots return distributions via violin plots by quantile.
- Can optionally annualize returns using `rate_of_ret=True`.

**Parameters**

- `factor_data` — MultiIndex factor data indexed by event dates.
- `returns` — Asset returns DataFrame.
- `avgretplot` — Window for event-study cumulative returns.
- `rate_of_ret` — Convert simple returns to annualized rates.
- `n_bars` — Number of time intervals for event distribution histogram.

**Returns**

Displays matplotlib figures for event analysis.

---

## Data model

All tear sheet functions expect `factor_data` to be a MultiIndex `DataFrame` with:

- Index: `(date, asset)`
- Columns:
  - Forward-return columns (e.g., `1D`, `5D`, `10D`)
  - `factor` — The factor values
  - `factor_quantile` — Quantile assignments
  - `group` (optional) — Asset group identifiers

This is the standard output format from `alphalens.utils.get_clean_factor_and_forward_returns()`.

## Dependencies and concepts

- **Visualization**: matplotlib, seaborn
- **Analysis**: pandas, numpy, scipy.stats, statsmodels
- **Internal**: `alphalens.plotting`, `alphalens.performance`, `alphalens.utils`

### Key tear sheet concepts

- **Long-short analysis**: Factor values are demeaned, creating equal-weight long and short sides.
- **Group-neutral analysis**: Asset groups are weighted equally, and returns are normalized within groups.
- **Quantile analysis**: Assets are divided into quantiles/buckets based on factor values; returns and metrics are computed per quantile.
- **Information Coefficient**: Spearman rank correlation between factor values and forward returns; higher IC indicates stronger predictive power.
- **Turnover**: Proportion of assets entering/leaving a quantile each period; low turnover suggests stable rankings.
- **Event study**: Analysis of returns in a window around specific factor events or signals.

## Practical usage

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

## Notes

- All tear sheets automatically apply consistent styling via the `@plotting.customize` decorator.
- GridFigure handles the layout complexity automatically; most workflows don't require direct use.
- The `by_group` parameter enables side-by-side or panel analysis when asset groups are present.
- For large datasets or many forward-return periods, tear sheets can take time to render; `create_summary_tear_sheet()` is faster for quick feedback.
- All plotting occurs within the tear sheet functions; call `plt.show()` or allow the Jupyter kernel to display results automatically.

