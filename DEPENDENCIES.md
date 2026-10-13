# Alphalens Function Dependencies

This document maps the in-package function calls in `src/alphalens`. It is
intended as a navigation aid for reviewing implementation changes: a change to
a lower-level function may affect every caller listed beneath it.

Dependencies below are direct calls between Alphalens functions. Calls into
NumPy, pandas, SciPy, statsmodels, matplotlib, seaborn, PIL, and empyrical
are not listed. Decorators (`customize`, `non_unique_bin_edges_error`) wrap
their decorated functions dynamically; those edges are called out separately.
The graph follows the checked-in source on branch `yzeng` (HEAD `7c375a3`)
and may need updating when functions are added or refactored.

## Table of Contents

- [Function dependency layers](#function-dependency-layers)
  - [Level 0 — foundational functions and values](#level-0--foundational-functions-and-values)
  - [Level 1 — shared operations and small composites](#level-1--shared-operations-and-small-composites)
  - [Level 2 — core analytics primitives](#level-2--core-analytics-primitives)
  - [Level 3 — composed analytics and the four core tear sheets](#level-3--composed-analytics-and-the-four-core-tear-sheets)
  - [Level 4 — end-to-end entry points](#level-4--end-to-end-entry-points)
  - [Level 5 — high-level wrappers (`alphalens.wrapper`)](#level-5--high-level-wrappers-alphalenswrapper)
- [Decorator / dynamic edges](#decorator--dynamic-edges)
- [Module dependency overview](#module-dependency-overview)
- [Key observations](#key-observations)

## Function dependency layers

Levels indicate the direction of dependency: higher-level functions rely on
lower-level functions. Functions within a level are grouped by purpose rather
than guaranteed to be entirely independent.

### Level 0 — foundational functions and values

These functions do not call another Alphalens function directly.

1. `alphalens.utils`: `add_custom_calendar_timedelta`,
   `backshift_returns_series`, `get_forward_returns_columns`,
   `infer_trading_calendar`, `make_naive_ts`, `print_table`,
   `quantize_factor`, `rate_of_return`, `rethrow`, `std_conversion`,
   `timedelta_strings_to_integers`, `timedelta_to_string`, `ic_autocor_adj`.
2. `alphalens.performance`: `common_start_returns`,
   `compute_mean_returns_spread`, `cumulative_returns`,
   `factor_rank_autocorrelation`, `factor_weights`, `quantile_turnover`.
3. `alphalens.plotting`: `axes_style`, `plotting_context`,
   `plot_cumulative_returns`, `plot_cumulative_returns_by_quantile`,
   `plot_events_distribution`, `plot_factor_rank_auto_correlation`,
   `plot_ic_by_group`, `plot_ic_hist`, `plot_ic_qq`, `plot_ic_ts`,
   `plot_monthly_ic_heatmap`, `plot_quantile_average_cumulative_return`,
   `plot_quantile_returns_bar`, `plot_quantile_returns_violin`,
   `plot_top_bottom_quantile_turnover`.
4. `alphalens.wrapper`: `call_with_matching_args` (filters kwargs by
   signature, then invokes the passed callable dynamically).

### Level 1 — shared operations and small composites

1. `utils.diff_custom_calendar_timedeltas` → `make_naive_ts`.
2. `utils.demean_forward_returns` → `get_forward_returns_columns`.
3. `utils.non_unique_bin_edges_error` → `rethrow` (decorator that wraps
   `quantize_factor` with a friendlier error message).
4. `performance.average_cumulative_return_by_quantile` →
   `common_start_returns`.
5. `performance.positions` → `add_custom_calendar_timedelta`.
6. `plotting.customize` → `axes_style`, `plotting_context` (decorator;
   dynamically invokes whichever plotting function it wraps).
7. `plotting.plot_information_table` → `ic_autocor_adj`, `print_table`.
8. `plotting.plot_quantile_statistics_table` → `print_table`.
9. `plotting.plot_returns_table` → `print_table`.
10. `plotting.plot_turnover_table` → `print_table`.
11. `extra.hit_rate` → `get_forward_returns_columns`.

### Level 2 — core analytics primitives

1. `utils.compute_forward_returns` → `diff_custom_calendar_timedeltas`,
   `infer_trading_calendar`, `timedelta_to_string`.
2. `utils.get_clean_factor` → `quantize_factor`.
3. `performance.factor_returns` → `factor_weights`,
   `get_forward_returns_columns`.
4. `performance.factor_information_coefficient` →
   `demean_forward_returns`, `get_forward_returns_columns`.
5. `performance.mean_return_by_quantile` → `demean_forward_returns`,
   `get_forward_returns_columns`.

### Level 3 — composed analytics and the four core tear sheets

1. `performance.factor_alpha_beta` → `factor_returns`,
   `get_forward_returns_columns`.
2. `performance.factor_cumulative_returns` → `cumulative_returns`,
   `factor_returns`, `get_forward_returns_columns`.
3. `performance.factor_positions` → `factor_weights`,
   `get_forward_returns_columns`, `positions`.
4. `performance.mean_information_coefficient` →
   `factor_information_coefficient`.
5. `tears.create_event_returns_tear_sheet` →
   `plot_quantile_average_cumulative_return`.
6. `tears.create_event_study_tear_sheet` →
   `create_event_returns_tear_sheet`, `plot_events_distribution`,
   `plot_quantile_returns_bar`, `plot_quantile_returns_violin`,
   `plot_quantile_statistics_table`.
7. `tears.create_information_tear_sheet` →
   `performance.factor_information_coefficient`,
   `performance.mean_information_coefficient`, `plot_ic_by_group`,
   `plot_ic_hist`, `plot_ic_qq`, `plot_ic_ts`, `plot_information_table`,
   `plot_monthly_ic_heatmap`.
8. `tears.create_returns_tear_sheet` → `performance.factor_returns`,
   `performance.mean_return_by_quantile`, `performance.factor_alpha_beta`,
   `plot_cumulative_returns`, `plot_cumulative_returns_by_quantile`,
   `plot_mean_quantile_returns_spread_time_series`,
   `plot_quantile_returns_bar`, `plot_quantile_returns_violin`,
   `plot_returns_table`.
9. `tears.create_summary_tear_sheet` → `performance.factor_returns`,
   `performance.mean_return_by_quantile`, `performance.factor_alpha_beta`,
   `performance.factor_information_coefficient`,
   `performance.mean_information_coefficient`,
   `performance.quantile_turnover`,
   `performance.factor_rank_autocorrelation`,
   `get_forward_returns_columns`, `plot_information_table`,
   `plot_quantile_returns_bar`, `plot_quantile_statistics_table`,
   `plot_returns_table`, `plot_turnover_table`.
10. `tears.create_turnover_tear_sheet` →
    `performance.quantile_turnover`,
    `performance.factor_rank_autocorrelation`,
    `get_forward_returns_columns`, `plot_factor_rank_auto_correlation`,
    `plot_top_bottom_quantile_turnover`, `plot_turnover_table`,
    `timedelta_strings_to_integers`.

### Level 4 — end-to-end entry points

1. `utils.get_clean_factor_and_forward_returns` →
   `compute_forward_returns`, `get_clean_factor`. This is the primary
   entry point users call to build `factor_data`.
2. `performance.create_pyfolio_input` → `factor_cumulative_returns`,
   `factor_positions`, `get_forward_returns_columns`. The bridge into
   `pyfolio-reloaded`.
3. `tears.create_full_tear_sheet` → `create_returns_tear_sheet`,
   `create_information_tear_sheet`, `create_turnover_tear_sheet`,
   `plot_quantile_statistics_table`.

### Level 5 — high-level wrappers (`alphalens.wrapper`)

These are the fork-specific convenience functions. They call public API
functions through the `alphalens.*` namespace and additionally thread
save-to-file paths and IC-type selection.

1. `wrapper.return_analysis_wrapper` →
   `performance.mean_return_by_quantile`,
   `tears.create_returns_tear_sheet` (when `tear_sheet_filepath` is set).
2. `wrapper.information_analysis_wrapper` →
   `performance.factor_information_coefficient` (called twice, once with
   `ic_type="spearman"` and once with `"pearson"`),
   `plotting.plot_information_table` (called twice, matching),
   `tears.create_information_tear_sheet` (when save path is set).
3. `wrapper.turnover_analysis_wrapper` →
   `performance.quantile_turnover`,
   `performance.factor_rank_autocorrelation`,
   `tears.create_turnover_tear_sheet` (when save path is set).
4. `wrapper.full_tear_sheet_wrapper` →
   `utils.get_forward_returns_columns`, `utils.get_clean_factor`,
   `wrapper.information_analysis_wrapper`,
   `wrapper.return_analysis_wrapper`,
   `wrapper.turnover_analysis_wrapper`. Iterates over a list of factor
   columns and aggregates the per-factor results into one combined table.

## Decorator / dynamic edges

Two functions do not appear as explicit `Call` nodes but shape the call
graph at runtime:

- `plotting.customize` wraps every public plotting function in
  `plotting.py` and every tear-sheet generator in `tears.py`. It applies
  the seaborn context, then invokes the wrapped function. Setting
  `set_context=False` at the call site skips the decorator.
- `utils.non_unique_bin_edges_error` wraps `utils.quantize_factor` to
  replace the raw pandas `ValueError` on non-unique bin edges with a
  more helpful message.
- `wrapper.call_with_matching_args` is a generic kwargs-filtering helper;
  it calls whatever callable is passed into it. In this codebase it is
  defined but the three workflow wrappers currently call their targets
  directly rather than going through it.

## Module dependency overview

```text
alphalens.extra
    └── hit_rate
        └── get_forward_returns_columns  (from utils)

alphalens.utils
    ├── calendar / timing primitives (infer, make_naive, timedelta_*)
    ├── data-prep pipeline: compute_forward_returns → get_clean_factor
    │       └── get_clean_factor_and_forward_returns (user entry point)
    └── shared helpers: get_forward_returns_columns, print_table,
        demean_forward_returns, rethrow

alphalens.performance
    ├── low-level stats: factor_weights, factor_returns, IC,
    │       mean_return_by_quantile, quantile_turnover, autocorrelation
    ├── composites: factor_alpha_beta, factor_cumulative_returns,
    │       factor_positions, mean_information_coefficient
    └── pyfolio bridge: create_pyfolio_input

alphalens.plotting
    ├── styling plumbing: customize (decorator), plotting_context,
    │       axes_style
    ├── table renderers: plot_returns_table, plot_turnover_table,
    │       plot_information_table, plot_quantile_statistics_table
    │       (all funnel through utils.print_table and
    │       utils.ic_autocor_adj)
    └── diagnostic plots: IC, quantile returns, cumulative returns,
            turnover, event windows

alphalens.tears
    ├── GridFigure (layout helper)
    ├── event-study tear sheets
    ├── four core tear sheets: summary / returns / information / turnover
    └── create_full_tear_sheet chains the four core sheets together

alphalens.wrapper
    └── thin, save-file-aware facades over the tears + performance
        public API; full_tear_sheet_wrapper loops over multiple
        factor columns and aggregates results
```

## Key observations

- `utils.get_forward_returns_columns` is the single most depended-upon
  function in the package: it is called by `demean_forward_returns`,
  `factor_information_coefficient`, `mean_return_by_quantile`,
  `factor_returns`, `factor_alpha_beta`, `factor_cumulative_returns`,
  `factor_positions`, `create_pyfolio_input`, `create_summary_tear_sheet`,
  `create_turnover_tear_sheet`, and `extra.hit_rate`. Any change to its
  column-detection regex affects nearly every analytics function.
- The analytics core is `performance.factor_returns`: `factor_alpha_beta`,
  `factor_cumulative_returns`, and `create_pyfolio_input` all build on it.
  It in turn depends on `factor_weights`, which is a pure function of
  `factor_data` (Level 0).
- `tears` is purely an orchestration layer: every tear sheet combines
  `performance.*` stats with `plotting.*` renders. No tear sheet performs
  its own numeric work.
- `wrapper` is the fork-specific add-on. It exists to (a) run both
  Spearman and Pearson IC in one shot, (b) auto-save tear sheets to PDF,
  and (c) loop over multiple factor columns. It does not introduce new
  analytics; it only re-exports existing public API with convenience.
- `extra.hit_rate` is a small, standalone metric that reuses
  `get_forward_returns_columns`; it is not part of any tear-sheet flow.
