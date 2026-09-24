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

### `call_with_matching_args(func, *args, **kwargs)`
Call a function after dropping unsupported keyword arguments.

**Behavior**

- Inspects `func` signature.
- Filters `kwargs` to accepted names.
- Preserves all positional args.

**Returns**

Whatever `func` returns.

## Workflow wrappers

### `return_analysis_wrapper(data, long_short=True, group_neutral=False, by_group=False, tear_sheet_filepath=None)`
Run return-oriented analysis and optionally save a return tear sheet.

**Arguments**

- `data` — Factor data in standard Alphalens cleaned format.
- `long_short` — Enable long-short style return analysis and corresponding weight demeaning path.
- `group_neutral` — Enable group-level normalization/de-meaning path for return analysis.
- `by_group` — Enable group-level breakout in return summaries/plots.
- `tear_sheet_filepath` — Optional output path for saving the return tear sheet.

**Behavior**

- Computes mean return by quantile and corresponding standard errors.
- Optionally calls `tears.create_returns_tear_sheet(..., save_file=tear_sheet_filepath)` when a filepath is provided.
- `long_short` affects factor weight construction: it is forwarded to `performance.factor_returns(...)`, then to `performance.factor_weights(..., demeaned=long_short, ...)`, so factor values are demeaned before normalization when enabled.
- `group_neutral` affects factor weight construction: it is forwarded to `performance.factor_returns(...)`, then to `performance.factor_weights(..., group_adjust=group_neutral, ...)`, enabling group-neutral weight construction when enabled.
- `by_group` does not affect factor weight construction: it controls group-level breakout of return summaries/plots, but is not used by `performance.factor_weights(...)`.

**Returns**

A dictionary with:

- `mean_return_by_q`
- `std_err_by_q`

---

### `information_analysis_wrapper(data, group_neutral=False, by_group=False, tear_sheet_filepath=None)`
Run IC analysis under both Spearman and Pearson definitions and optionally save an information tear sheet.

**Arguments**

- `group_neutral` — If `True`, demean forward returns by group before computing the Information Coefficient.
- `by_group` — If `True`, compute and display IC statistics separately for each group rather than as one pooled result.
- `tear_sheet_filepath` — Optional output path for saving the information tear sheet.

**Behavior**

- Computes daily IC via `performance.factor_information_coefficient(..., ic_type="spearman")`.
- Computes daily IC via `performance.factor_information_coefficient(..., ic_type="pearson")`.
- Summarizes each IC table via `plotting.plot_information_table(..., as_figure=False, return_df=True)`.
- IC autocorrelation-adjusted diagnostics are added inside `plotting.plot_information_table(...)`, which calls `utils.ic_autocor_adj(ic_data, lag=1)` before returning the summary table.
- Optionally saves an information tear sheet when filepath is provided.

**Returns**

A dictionary with:

- `ic_spearman`
- `ic_pearson`

Each value is a `DataFrame` containing summary statistics and lag-1 autocorrelation diagnostics.

---

### `turnover_analysis_wrapper(data, turnover_period, period_unit, tear_sheet_filepath=None)`
Run turnover diagnostics and optionally save a turnover tear sheet.

**Arguments**

- `data` — Factor data in standard Alphalens cleaned format.
- `turnover_period` — Number of periods for turnover analysis.
- `period_unit` — Time unit for turnover analysis (for example `"D"`, `"W"`, `"M"`).
- `tear_sheet_filepath` — Optional output path for saving the turnover tear sheet.

**Behavior**

- Computes per-quantile turnover for the selected period.
- Computes factor rank autocorrelation for the same period.
- Optionally calls `tears.create_turnover_tear_sheet(...)` with `turnover_periods=[f"{turnover_period}{period_unit}"]`.

**Returns**

A dictionary with:

- `turnover`
- `factor_autocorr`

---

### `full_tear_sheet_wrapper(data, factors, fwd_rtrn_cols, output_dir, long_short=True, group_neutral=False, by_group=False, turnover_period=1, period_unit="D")`
Wrapper for alphalens full tear sheet function.

**Arguments**

- `data` — Factor data in the format expected by alphalens.
- `factors` — List of factor column names to analyze.
- `fwd_rtrn_cols` — List of forward return column names to analyze.
- `output_dir` — Directory to save tear sheets; each factor gets its own output files.
- `long_short` — Whether to perform long-short analysis. When `True`, returns are demeaned across the full universe so analysis reflects a long/short factor portfolio rather than a raw long-only one.
- `group_neutral` — Whether to demean forward returns by group during information/return analysis; forwarded to lower-level wrappers.
- `by_group` — Whether to compute/display statistics separately by group; forwarded to lower-level wrappers.
- `turnover_period` — Number of periods for turnover analysis.
- `period_unit` — Unit of time for turnover analysis (default: `"D"`).

**Behavior**

- Validates that `data` contains `date` and `asset`, then sets a MultiIndex (`date`, `asset`).
- Validates forward-return columns against `fwd_rtrn_cols`.
- For each factor in `factors`:
  - Renames that factor column to `factor`.
  - Runs `information_analysis_wrapper(...)` with `group_neutral` and `by_group`, and saves an information tear sheet.
  - Builds cleaned factor data with `utils.get_clean_factor(...)`.
  - Runs `return_analysis_wrapper(...)` with `long_short`, `group_neutral`, and `by_group`, then saves return and turnover tear sheets.
- Concatenates per-factor outputs into combined result tables.

**Returns**

A dictionary containing information coefficient, return analysis, and turnover DataFrames for each factor with keys:

- `ic_spearman`
- `ic_pearson`
- `mean_return_by_q`
- `std_err_by_q`
- `turnover`
- `factor_autocorr`

## Practical example

```python
import alphalens

factor_data = ...  # output from alphalens.utils.get_clean_factor_and_forward_returns(...)

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

full = alphalens.wrapper.full_tear_sheet_wrapper(
	data=raw_factor_frame,
	factors=["factor_a", "factor_b"],
	fwd_rtrn_cols=["1D", "5D", "10D"],
	output_dir="tear_sheets",
	long_short=True,
	group_neutral=True,
	by_group=True,
	turnover_period=5,
	period_unit="D",
)
```

## Notes

- The wrappers prioritize convenience over configurability while still exposing the main analysis flags (`long_short`, `group_neutral`, `by_group`) in wrapper APIs.
- `tear_sheet_filepath` is optional in practice: when falsey (for example `None` or empty string), wrappers skip saving.
- This module is imported at package level, so wrappers are available as `alphalens.wrapper`.
