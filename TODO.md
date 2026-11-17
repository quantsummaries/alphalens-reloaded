# Alphalens Reloaded — Maintenance TODO

## Table of Contents

- [Bugs / behavior fixes](#bugs-behavior-fixes)
- [Test coverage gaps](#test-coverage-gaps)
- [Documentation](#documentation)
- [Understanding Event Study Code](#understanding-event-study-code)

This file tracks **work to do on the codebase itself**: bugs, missing tests,
stale docs, upstream features to port, performance fixes.

The **learning roadmap** (for someone coming to the codebase fresh) lives in
[`CODE_LEARN.md`](CODE_LEARN.md). Project-wide conventions:
[`../PROJECT-CONVENTIONS.md`](../PROJECT-CONVENTIONS.md).

<a id="bugs-behavior-fixes"></a>

## Bugs / behavior fixes · [Back To TOC](#table-of-contents)

- [ ] None

<a id="test-coverage-gaps"></a>

## Test coverage gaps · [Back To TOC](#table-of-contents)

- [ ] Promote `tests/test_wrapper.py` (currently script-style helpers only,
      `pytest tests/test_wrapper.py` collects 0 items) into real `test_*`
      functions covering `return_analysis_wrapper`,
      `information_analysis_wrapper`, `turnover_analysis_wrapper`,
      `full_tear_sheet_wrapper`, including the save-file path. (Partial: a
      new `tests/test_information_display.py` covers the `tables_as_figures`
      table-display path.)
- [ ] Validate the `hit_rate` calculation in `src/alphalens/extra.py` and
      the coverage in `tests/test_extra.py`.

<a id="documentation"></a>

## Documentation · [Back To TOC](#table-of-contents)

- [ ] None

<a id="understanding-event-study-code"></a>

## Understanding Event Study Code · [Back To TOC](#table-of-contents)

The event-study code spans three modules:

| Function | Role | Source |
| --- | --- | --- |
| `create_event_study_tear_sheet()` | Complete report: event counts, cumulative event curves, and quantile-return plots. | [tears.py:913](src/alphalens/tears.py#L913) |
| `create_event_returns_tear_sheet()` | Event-window cumulative-return charts, optionally by group. | [tears.py:807](src/alphalens/tears.py#L807) |
| `average_cumulative_return_by_quantile()` | Computes event-path means and standard deviations by quantile. | [performance.py:917](src/alphalens/performance.py#L917) |
| `common_start_returns()` | Extracts windows around event dates and rebases each asset's path to zero. | [performance.py:819](src/alphalens/performance.py#L819) |
| `cumulative_returns()` | Compounds simple returns into wealth before event windows are normalized. | [performance.py:472](src/alphalens/performance.py#L472) |
| `plot_quantile_average_cumulative_return()` | Draws event curves and optional error bars. | [plotting.py:1092](src/alphalens/plotting.py#L1092) |
| `plot_events_distribution()` | Draws event counts over time, including the single-date case. | [plotting.py:1203](src/alphalens/plotting.py#L1203) |

**Main calculation path**

```text
create_event_study_tear_sheet
├── plot_events_distribution
└── create_event_returns_tear_sheet
    ├── average_cumulative_return_by_quantile
    │   ├── cumulative_returns
    │   └── common_start_returns
    └── plot_quantile_average_cumulative_return
```

For understanding the mathematics, start with `common_start_returns()`, then
read `average_cumulative_return_by_quantile()`.

**Example**

```python
from alphalens import tears

daily_returns = prices.pct_change(fill_method=None)

tears.create_event_returns_tear_sheet(
    factor_data,
    daily_returns,
    avgretplot=(5, 15),
    long_short=False,
)
```

The window includes up to five observations before and fifteen after each
event. Event time zero has return zero. The input return data should extend
beyond the event dates to cover this window.
