# `alphalens.wrapper`

High-level convenience wrappers that orchestrate common Alphalens workflows (returns, information, and turnover analysis) and optionally save tear sheets to file.

This module sits on top of `alphalens.performance`, `alphalens.plotting`, and `alphalens.tears` and is intended for quick end-to-end analysis with fewer manual function calls.

## Input data expectation

All wrapper entry points expect `data` in standard Alphalens cleaned format, typically produced by:

- `alphalens.utils.get_clean_factor_and_forward_returns(...)`

That means:

- MultiIndex index: `(date, asset)`
- Columns include at least: forward-return horizons, `factor`, `factor_quantile`
- Optional `group` column for group-aware analysis

## Utility helpers

### `ic_autocor_adj(daily_ic, lag=5)`
Compute autocorrelation diagnostics and HAC-adjusted significance metrics for each IC horizon.

**Behavior**

- Computes lag-`lag` autocorrelation of each IC series.
- Runs Ljung-Box test (`acorr_ljungbox`) at the selected lag.
- Fits constant-only OLS with HAC/Newey-West covariance and reports adjusted t-stat and p-value.

**Returns**

A `DataFrame` indexed by metric name (`lag{lag}_autocorr`, `lb_pvalue`, `nw_tstat`, `nw_pvalue`) with one column per horizon.

---

### `call_with_matching_args(func, *args, **kwargs)`
Call a function after dropping unsupported keyword arguments.

**Behavior**

- Inspects `func` signature.
- Filters `kwargs` to accepted names.
- Preserves all positional args.

**Returns**

Whatever `func` returns.

## Workflow wrappers

### `return_analysis_wrapper(data, tear_sheet_filepath)`
Run return-oriented analysis and optionally save a return tear sheet.

**Behavior**

- Computes mean return by quantile and corresponding standard errors.
- Optionally calls `tears.create_returns_tear_sheet(..., save_file=tear_sheet_filepath)` when a filepath is provided.

**Returns**

A dictionary with:

- `mean_return_by_q`
- `std_err_by_q`

---

### `information_analysis_wrapper(data, tear_sheet_filepath)`
Run IC analysis under both Spearman and Pearson definitions and optionally save an information tear sheet.

**Behavior**

- Computes daily IC via `performance.factor_information_coefficient(..., ic_type="spearman")`.
- Computes daily IC via `performance.factor_information_coefficient(..., ic_type="pearson")`.
- Summarizes each IC table via `plotting.plot_information_table(..., as_figure=False, return_df=True)`.
- Appends autocorrelation-adjusted diagnostics from `ic_autocor_adj(..., lag=1)`.
- Optionally saves an information tear sheet when filepath is provided.

**Returns**

A dictionary with:

- `ic_spearman`
- `ic_pearson`

Each value is a `DataFrame` containing summary statistics and lag-1 autocorrelation diagnostics.

---

### `turnover_analysis_wrapper(data, turnover_period, period_unit, tear_sheet_filepath)`
Run turnover diagnostics and optionally save a turnover tear sheet.

**Behavior**

- Computes per-quantile turnover for the selected period.
- Computes factor rank autocorrelation for the same period.
- Optionally calls `tears.create_turnover_tear_sheet(...)` with `turnover_periods=[f"{turnover_period}{period_unit}"]`.

**Returns**

A dictionary with:

- `turnover`
- `factor_autocorr`

## Practical example

```python
import alphalens

# factor_data is output from alphalens.utils.get_clean_factor_and_forward_returns(...)

ret = alphalens.wrapper.return_analysis_wrapper(
	data=factor_data,
	tear_sheet_filepath="returns_tear_sheet.png",
)

ic = alphalens.wrapper.information_analysis_wrapper(
	data=factor_data,
	tear_sheet_filepath="information_tear_sheet.pdf",
)

to = alphalens.wrapper.turnover_analysis_wrapper(
	data=factor_data,
	turnover_period=5,
	period_unit="D",
	tear_sheet_filepath="turnover_tear_sheet.png",
)
```

## Notes

- The wrappers prioritize convenience over configurability; they use fixed defaults such as `long_short=True` and `group_neutral=False` in their internal tear-sheet calls.
- `tear_sheet_filepath` is optional in practice: when falsey (for example `None` or empty string), wrappers skip saving.
- This module is imported at package level, so wrappers are available as `alphalens.wrapper`.

