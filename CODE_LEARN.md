# Alphalens Reloaded — Learning Roadmap

Entry-points and recommended reading order for learning this codebase.
All paths below are relative to the repo root `alphalens-reloaded/`.

Companion docs: `CODE_OVERVIEW.md` (module-by-module writeup + known findings),
`docs/pdoc/alphalens/*.html` (pdoc-generated API reference).

## Table of Contents

- [0. Layout at a glance](#0-layout-at-a-glance)
  - [Source modules (`src/alphalens/`, by size)](#source-modules-src-alphalens-by-size)
  - [Tests (`tests/`)](#tests-tests)
  - [Official example notebooks (`docs/source/notebooks/`)](#official-example-notebooks-docs-source-notebooks)
- [1. Setup and orientation](#1-setup-and-orientation)
- [2. Lock in the data model (do this before any module)](#2-lock-in-the-data-model-do-this-before-any-module)
- [3. Run the overview notebook end-to-end FIRST](#3-run-the-overview-notebook-end-to-end-first)
- [4. `alphalens.utils` — data preparation](#4-alphalensutils-data-preparation)
- [5. `alphalens.performance` — analytics core](#5-alphalensperformance-analytics-core)
- [6. `alphalens.plotting` — visualization](#6-alphalensplotting-visualization)
- [7. `alphalens.tears` — assembled reports](#7-alphalensteears-assembled-reports)
- [8. `alphalens.wrapper` — high-level shortcuts](#8-alphalenswrapper-high-level-shortcuts)
- [9. `alphalens.extra` — small helpers](#9-alphalensextra-small-helpers)
- [10. Cross-repo integration](#10-cross-repo-integration)
- [11. Known quirks / pitfalls to watch for](#11-known-quirks-pitfalls-to-watch-for)
- [Suggested order](#suggested-order)

## 0. Layout at a glance

### Source modules (`src/alphalens/`, by size)

| File | Size | Role |
|---|---:|---|
| `performance.py` | 48 KB | Analytics core: IC, factor returns, quantile stats, event studies |
| `utils.py` | 45 KB | Data prep: forward returns, quantile binning, calendar helpers |
| `plotting.py` | 32 KB | All matplotlib/seaborn visualizations |
| `tears.py` | 30 KB | Assembled tear sheets |
| `wrapper.py` | 16 KB | High-level end-to-end wrappers (new, in-progress) |
| `extra.py` | 2.4 KB | Small helpers (see `tests/test_extra.py`) |

Public API (`__init__.py`): `from alphalens import utils, performance, plotting, tears, wrapper, extra`.

### Tests (`tests/`)

| File | Size | Notes |
|---|---:|---|
| `test_performance.py` | 52 KB | Best coverage — read alongside `performance.py` |
| `test_utils.py` | 27 KB | Read alongside `utils.py` |
| `test_overview.py` | 15 KB | End-to-end smoke tests |
| `test_tears.py` | 14 KB | Tear sheet rendering tests |
| `test_wrapper.py` | 7.2 KB | **Script-style only** — no `test_*` functions (known gap) |
| `test_extra.py` | 2 KB | |

### Official example notebooks (`docs/source/notebooks/`)

- [x] `overview.ipynb` — the canonical end-to-end walkthrough.
- [x] `pyfolio_integration.ipynb` — how factor data flows into pyfolio.
- [ ] `event_study.ipynb` — event-study variant.
- [ ] `intraday_factor.ipynb` — intraday / sub-daily factors.

[⬆ 回到目录](#table-of-contents)

## 1. Setup and orientation

- [x] Verify editable install: `python -c "import alphalens; print(alphalens.__file__)"`
      should point into `src/alphalens/`.
- [x] Run the test suite green: `pytest tests/ -q` (expect `test_wrapper.py`
      to collect 0 items — that is a known gap, not a failure).
- [x] Open `README.md` and skim `docs/source/api-reference` (or the pdoc HTML
      under `docs/pdoc/alphalens/index.html`).
- [x] Read `CODE_OVERVIEW.md` §Overview and §alphalens.wrapper for the pipeline
      shape before opening any source file.

[⬆ 回到目录](#table-of-contents)

## 2. Lock in the data model (do this before any module)

Alphalens is opinionated about one thing: its internal `factor_data` object.
Everything downstream consumes it.

- [x] The index is a `MultiIndex` with level 0 = `date`, level 1 = `asset`.
- [x] Columns typically include:
  - `factor` — the raw factor value,
  - `factor_quantile` — integer bin (1..quantiles),
  - `group` (optional) — asset-group label,
  - forward-return columns named like `1D`, `5D`, `10D`, `30m`, `1D1h`
    (Timedelta-compatible strings).
- [x] Forward-return columns are detected by
      `utils.get_forward_returns(...)` — read that function to understand the
      naming convention.
- [ ] Sanity-check: reproduce the `factor_data` MultiIndex shape from
      `tests/test_utils.py` (e.g. the `factor_data` fixture) and print
      `.head()`, `.index.names`, `.columns` to confirm.

[⬆ 回到目录](#table-of-contents)

## 3. Run the overview notebook end-to-end FIRST

Before reading any implementation, see the whole pipeline run on real data.

- [x] Open `docs/source/notebooks/overview.ipynb` and execute top-to-bottom.
- [x] Identify the call to `get_clean_factor_and_forward_returns` and the
      call to each tear sheet.
- [x] Match each rendered chart to the function that produced it (use the
      pdoc HTML or `tears.py` as a map).
- [x] Note where `wrapper.return_analysis_wrapper` /
      `information_analysis_wrapper` / `turnover_analysis_wrapper` are used
      vs. calling `tears.create_*_tear_sheet` directly.

[⬆ 回到目录](#table-of-contents)

## 4. `alphalens.utils` — data preparation

- [x] Start with the one-stop entry point:
      `utils.get_clean_factor_and_forward_returns(...)`. Read its body; it is a
      thin composition of `compute_forward_returns` + `get_clean_factor`.
- [x] Read `compute_forward_returns(...)` — timezone checks, calendar
      inference, period alignment.
- [x] Read `quantize_factor(...)` — quantile vs. bin, `by_group`,
      `zero_aware`, `no_raise`.
- [ ] Read `MaxLossExceededError` and `NonMatchingTimezoneError` — the two
      exceptions users actually hit.
- [ ] Skim the calendar/time helpers (`infer_trading_calendar`,
      `add_custom_calendar_timedelta`, `make_naive_ts`, …) — you do not need
      to memorize them; just know they exist.
- [ ] Cross-read `tests/test_utils.py` for concrete input/output shapes.

[⬆ 回到目录](#table-of-contents)

## 5. `alphalens.performance` — analytics core

Read in this order; each group builds on the previous one.

- [x] **Information Coefficient**: `factor_information_coefficient`,
      `mean_information_coefficient`. Note the `ic_type="spearman"|"pearson"`
      parameter (this fork's addition).
- [x] **Factor weights & returns**: `factor_weights`, `factor_returns`.
      Work through the worked example in `CODE_OVERVIEW.md` §3.3.2 by hand to
      internalize the `w·r` portfolio math.
- [x] **Alpha / beta vs. universe**: `factor_alpha_beta`.
- [x] **Quantile analysis**: `mean_return_by_quantile`,
      `compute_mean_returns_spread`.
- [x] **Turnover & rank stability**: `quantile_turnover`,
      `factor_rank_autocorrelation`.
- [ ] **Event studies**: `common_start_returns`,
      `average_cumulative_return_by_quantile`.
- [ ] **Pyfolio bridge**: `create_pyfolio_input` — what tuple it returns
      `(returns, positions, benchmark)` and why this is the integration point
      with `pyfolio-reloaded`.
- [ ] Cross-read `tests/test_performance.py` (52 KB — the densest, most
      instructive test file in the repo).

[⬆ 回到目录](#table-of-contents)

## 6. `alphalens.plotting` — visualization

- [ ] Read `customize`, `plotting_context`, `axes_style` — the seaborn
      plumbing every plot inherits.
- [ ] Group plots by purpose (matches `CODE_OVERVIEW.md` §4):
  - [ ] Table displays: `plot_returns_table`, `plot_turnover_table`,
        `plot_information_table`, `plot_quantile_statistics_table`
        (note the `return_df` / `as_figure` contract).
  - [ ] IC plots: `plot_ic_ts`, `plot_ic_hist`, `plot_ic_qq`,
        `plot_ic_by_group`, `plot_monthly_ic_heatmap`.
  - [ ] Returns: `plot_quantile_returns_bar`, `plot_quantile_returns_violin`,
        `plot_mean_quantile_returns_spread_time_series`,
        `plot_cumulative_returns`, `plot_cumulative_returns_by_quantile`,
        `plot_quantile_average_cumulative_return`.
  - [ ] Factor characteristics: `plot_factor_rank_auto_correlation`,
        `plot_top_bottom_quantile_turnover`, `plot_events_distribution`.
- [ ] Note the color conventions (`DECIMAL_TO_BPS = 10000`, reversed coolwarm,
      colorblind palette) — they are consistent across all plots.

[⬆ 回到目录](#table-of-contents)

## 7. `alphalens.tears` — assembled reports

- [ ] Read `GridFigure` (helper class for subplot layout).
- [ ] Read each entry point in this order (each adds one layer):
  - [ ] `create_summary_tear_sheet` — compact overview.
  - [ ] `create_returns_tear_sheet` — returns-focused.
  - [ ] `create_information_tear_sheet` — IC-focused.
  - [ ] `create_turnover_tear_sheet` — turnover/autocorrelation.
  - [ ] `create_full_tear_sheet` — the above chained together.
  - [ ] `create_event_returns_tear_sheet` / `create_event_study_tear_sheet`
        — event-study variants.
- [ ] Pay attention to `return_df` / `save_file` parameters. Re-read the
      two open findings in `CODE_OVERVIEW.md` (info/turnover tear sheets do not
      honor `return_df` the way their signatures suggest).

[⬆ 回到目录](#table-of-contents)

## 8. `alphalens.wrapper` — high-level shortcuts

- [ ] Read `ic_autocor_adj` and `call_with_matching_args` (utility helpers).
- [ ] Read the three workflow wrappers:
  - [ ] `return_analysis_wrapper(data, tear_sheet_filepath)`
  - [ ] `information_analysis_wrapper(data, tear_sheet_filepath)`
  - [ ] `turnover_analysis_wrapper(data, turnover_period, period_unit, tear_sheet_filepath)`
- [ ] Compare what each wrapper does vs. the equivalent direct call through
      `tears.create_*_tear_sheet` — identify the value-add (typically:
      autocorrelation-adjusted diagnostics + automatic save-to-file).

[⬆ 回到目录](#table-of-contents)

## 9. `alphalens.extra` — small helpers

- [ ] Read `src/alphalens/extra.py` (2.4 KB — quick).
- [ ] Read `tests/test_extra.py` to see the contract.

[⬆ 回到目录](#table-of-contents)

## 10. Cross-repo integration

- [ ] Trace `performance.create_pyfolio_input(...)` into
      `pyfolio-reloaded/src/pyfolio/` — find which pyfolio entry point
      consumes its `(returns, positions, benchmark)` tuple.
- [ ] Note how `alphalens` delegates statistics to `empyrical-reloaded`
      (grep `import empyrical` / `from empyrical`).

[⬆ 回到目录](#table-of-contents)

## 11. Known quirks / pitfalls to watch for

From `CODE_OVERVIEW.md` (re-verified 2026-10-09 at HEAD `7c375a3`):

- [ ] `create_information_tear_sheet(..., return_df=True)` still returns a
      figure because `as_figure=True` is hard-coded downstream.
- [ ] `create_turnover_tear_sheet(..., return_df=True)` discards the table
      returned by `plot_turnover_table`.
- [ ] `tests/test_wrapper.py` is script-style — run it directly, not via
      pytest, until it gets real `test_*` functions.
- [ ] `filter_zscore` in `utils.get_clean_factor_and_forward_returns` can
      introduce lookahead bias — understand when it is safe to use.

[⬆ 回到目录](#table-of-contents)

## Suggested order

1. Setup + green tests (§1).
2. Reproduce the `factor_data` MultiIndex shape from `tests/test_utils.py`
   (§2) — 15 min.
3. Run `docs/source/notebooks/overview.ipynb` end-to-end (§3).
4. Walk `utils.py` → `performance.py` → `plotting.py` → `tears.py` (§4–§7).
5. Skim `wrapper.py` and `extra.py` (§8–§9).
6. Cross-repo traces (§10).
7. Leave the known quirks (§11) as an open checklist.

[⬆ 回到目录](#table-of-contents)
