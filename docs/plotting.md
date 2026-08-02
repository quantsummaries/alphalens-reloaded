# `alphalens.plotting`

Visualization utilities for factor research, including plots for Information Coefficient analysis, factor returns, quantile performance, and other diagnostic charts. The module provides publication-quality visualizations with sane defaults for the Alphalens workflow.

This module visualizes the outputs from `alphalens.performance` and the cleaned factor data from `alphalens.utils`.

## Styling and context management

### `customize(func)` — decorator
Apply default plotting context and style to a function.

**Behavior**

- Sets seaborn colorblind-friendly palette.
- Applies default plotting context and axes style.
- Can be disabled with `set_context=False` in the decorated function call.

---

### `plotting_context(context="notebook", font_scale=1.5, rc=None)`
Create an alphalens-specific plotting context.

**Behavior**

- Wraps `seaborn.plotting_context()` with alphalens defaults.
- Default line width is 1.5.
- Can be used as a context manager for multiple plots.

**Returns**

A seaborn plotting context object suitable for use in `with` statements.

---

### `axes_style(style="darkgrid", rc=None)`
Create an alphalens-specific axes style context.

**Behavior**

- Wraps `seaborn.axes_style()` with alphalens defaults.
- Commonly used with `plotting_context()`.

**Returns**

A seaborn axes style object suitable for use in `with` statements.

## Data table displays

### `plot_returns_table(alpha_beta, mean_ret_quantile, mean_ret_spread_quantile, return_df=False)`
Display a summary table of factor portfolio returns, alpha, beta, and quantile statistics.

**Behavior**

- Combines alpha/beta results with quantile return statistics.
- Converts decimal returns to basis points.
- Prints a formatted table or returns as a `DataFrame`.

**Returns**

Pretty-printed table or a `DataFrame` when `return_df=True`.

---

### `plot_turnover_table(autocorrelation_data, quantile_turnover, return_df=False)`
Display quantile turnover and factor rank autocorrelation statistics.

**Behavior**

- Shows mean turnover for each quantile by period.
- Shows mean factor rank autocorrelation.
- Prints formatted tables or returns as `DataFrame`s.

**Returns**

Printed tables or a pair of `DataFrame`s when `return_df=True`.

---

### `plot_information_table(ic_data, return_df=False)`
Display Information Coefficient summary statistics.

**Behavior**

- Computes IC mean, standard deviation, risk-adjusted IC, and t-statistics.
- Includes skewness and kurtosis.
- Prints a summary table or returns as a `DataFrame`.

**Returns**

Pretty-printed table or a `DataFrame` when `return_df=True`.

---

### `plot_quantile_statistics_table(factor_data, return_df=False)`
Display factor value statistics by quantile.

**Behavior**

- Groups factor data by `factor_quantile`.
- Reports min, max, mean, standard deviation, and count per quantile.
- Includes count percentages.

**Returns**

Pretty-printed table or a `DataFrame` when `return_df=True`.

## Information Coefficient visualization

### `plot_ic_ts(ic, ax=None)`
Plot the Information Coefficient time series with a rolling 22-day average.

**Behavior**

- Creates one subplot per forward-return period.
- Overlays daily IC and a 22-day moving average.
- Includes mean and standard deviation annotations.
- Aligns y-axis ranges across subplots.

**Returns**

A numpy array of matplotlib axes.

---

### `plot_ic_hist(ic, ax=None)`
Plot IC as a histogram with kernel density estimate.

**Behavior**

- Creates a 3-column grid of histograms, one per forward-return period.
- Includes KDE overlay and a vertical line at the mean.
- Clamps x-axis to `[-1, 1]`.

**Returns**

A numpy array of matplotlib axes.

---

### `plot_ic_qq(ic, theoretical_dist=scipy.stats.norm, ax=None)`
Plot IC values against a theoretical distribution using a Q-Q plot.

**Behavior**

- Creates a 3-column grid of Q-Q plots.
- Supports normal and Student-t distributions.
- Uses `statsmodels.qqplot()` for plotting.

**Returns**

A numpy array of matplotlib axes.

---

### `plot_ic_by_group(ic_group, ax=None)`
Plot IC by group as a bar chart.

**Behavior**

- Shows mean IC for each group.
- Rotates x-axis labels for readability.

**Returns**

A matplotlib axes object.

---

### `plot_monthly_ic_heatmap(mean_monthly_ic, ax=None)`
Plot IC or returns as a month/year heatmap with color coding.

**Behavior**

- Creates one heatmap per forward-return period.
- Uses reversed coolwarm colormap (red = negative, blue = positive).
- Annotates cell values.
- Centered at 0.

**Returns**

A numpy array of matplotlib axes.

## Returns analysis

### `plot_quantile_returns_bar(mean_ret_by_q, by_group=False, ylim_percentiles=None, ax=None)`
Plot mean returns by factor quantile as a bar chart.

**Behavior**

- Optionally creates separate subplots for each group.
- Can limit y-axis range using percentiles of observed data.
- Converts to basis points.

**Returns**

A matplotlib axes object or array depending on grouping.

---

### `plot_quantile_returns_violin(return_by_q, ylim_percentiles=None, ax=None)`
Plot return distributions by factor quantile using violin plots.

**Behavior**

- Shows distribution of returns within each quantile across periods.
- Uses seaborn violin plot with quartile indicators.
- Optionally limits y-axis range using percentiles.

**Returns**

A matplotlib axes object.

---

### `plot_mean_quantile_returns_spread_time_series(mean_returns_spread, std_err=None, bandwidth=1, ax=None)`
Plot the top-minus-bottom quantile return spread over time.

**Behavior**

- Shows the difference between top and bottom quantile returns period by period.
- Overlays a 22-day rolling average.
- Optionally adds confidence bands based on standard error.
- Symmetrizes y-axis around zero at the 95th percentile.

**Returns**

A matplotlib axes object or array if input is a `DataFrame`.

---

### `plot_cumulative_returns(factor_returns, period, freq=None, title=None, ax=None)`
Plot cumulative returns of a factor-weighted portfolio.

**Behavior**

- Converts simple returns to cumulative using `performance.cumulative_returns()`.
- Includes a reference line at 1.0 (break-even).
- Displays the forward-return period in the title.

**Returns**

A matplotlib axes object.

---

### `plot_cumulative_returns_by_quantile(quantile_returns, period, freq=None, ax=None)`
Plot cumulative returns separately for each factor quantile.

**Behavior**

- Uses reversed coolwarm colormap for quantile coloring.
- Uses symmetric log scale on the y-axis for readability across wide ranges.
- Shows all quantiles on a single plot with a legend.

**Returns**

A matplotlib axes object.

---

### `plot_quantile_average_cumulative_return(avg_cumulative_returns, by_quantile=False, std_bar=False, title=None, ax=None)`
Plot average cumulative returns by factor quantile around event dates.

**Behavior**

- Shows mean cumulative returns across the event window for each quantile.
- Optionally creates separate subplots per quantile for clarity.
- Can overlay standard deviation error bars.
- Uses reversed coolwarm colormap for consistency.
- Marks event date (x=0) with a vertical dashed line.

**Returns**

A matplotlib axes object or array.

## Factor characteristics

### `plot_factor_rank_auto_correlation(factor_autocorrelation, period=1, ax=None)`
Plot factor rank autocorrelation over time.

**Behavior**

- Shows the stability of relative factor rankings.
- Includes a reference line at 0 (no autocorrelation).
- Annotates the mean autocorrelation in a text box.

**Returns**

A matplotlib axes object.

---

### `plot_top_bottom_quantile_turnover(quantile_turnover, period=1, ax=None)`
Plot turnover for the top and bottom quantiles over time.

**Behavior**

- Extracts the maximum and minimum quantiles.
- Shows the proportion of names new to each quantile each period.
- Useful for detecting data quality or stationarity issues.

**Returns**

A matplotlib axes object.

---

### `plot_events_distribution(events, num_bars=50, ax=None)`
Plot the distribution of factor events across time.

**Behavior**

- Divides the time span into `num_bars` intervals.
- Counts events in each interval.
- Displays as a bar chart.

**Returns**

A matplotlib axes object.

## Constants

### `DECIMAL_TO_BPS = 10000`
Conversion factor for decimal returns to basis points. Used throughout the module when displaying returns-related plots.

## Dependencies and conventions

- **Visualization**: seaborn, matplotlib, scipy.stats
- **Analysis**: pandas, numpy, statsmodels
- **Internal**: `alphalens.utils`, `alphalens.performance`

### Color conventions

- **Coolwarm reversed**: Red represents low/negative quantiles; blue represents high/positive quantiles.
- **Colorblind palette**: All plots use seaborn's colorblind palette for accessibility.
- **Line colors**: Green (forestgreen) for means and averages; blue (steelblue) for confidence bands; red (orangered) for rolling averages.

### Plot conventions

- **Multi-subplot layouts**: Plots with multiple periods or groups create grid layouts (usually 1×3 or 2×2).
- **Shared axes**: Where applicable, y-axes are shared across subplots to aid comparison.
- **Reference lines**: Zero lines are included on relevant plots to indicate break-even or neutral positions.
- **Log scales**: Cumulative returns plots use symmetric log scale (`symlog`) to handle very large or very small returns.
- **Annotations**: Statistical summaries (mean, std dev) are included in text boxes on many plots.

## Practical usage

Typical workflow:

1. Compute factor diagnostics with `alphalens.performance` functions.
2. Call plotting functions with the results.
3. All plotting functions are decorated with `@customize` to apply consistent styling.
4. Optional: use `set_context=False` in any plotting call to skip automatic styling.

Example call: `plot_ic_ts(ic_data)` or `plot_quantile_returns_bar(mean_ret_by_q)`.

## Notes

- All plotting functions accept an optional `ax` parameter for custom subplot layouts.
- Return values vary: some functions print tables directly, others return `DataFrame`s or axes.
- The `return_df=False` parameter on table functions controls printing vs. returning.
- Most functions are designed for Jupyter notebooks but work in any matplotlib environment.

