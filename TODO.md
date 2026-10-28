# Alphalens Reloaded — Maintenance TODO

This file tracks **work to do on the codebase itself**: bugs, missing tests,
stale docs, upstream features to port, performance fixes.

The **learning roadmap** (for someone coming to the codebase fresh) lives in
[`CODE_LEARN.md`](CODE_LEARN.md). Project-wide conventions:
[`../PROJECT-CONVENTIONS.md`](../PROJECT-CONVENTIONS.md).

## Bugs / behavior fixes

- [ ] None

## Test coverage gaps

- [ ] Promote `tests/test_wrapper.py` (currently script-style helpers only,
      `pytest tests/test_wrapper.py` collects 0 items) into real `test_*`
      functions covering `return_analysis_wrapper`,
      `information_analysis_wrapper`, `turnover_analysis_wrapper`,
      `full_tear_sheet_wrapper`, including the save-file path. (Partial: a
      new `tests/test_information_display.py` covers the `tables_as_figures`
      table-display path.)
- [ ] Validate the `hit_rate` calculation in `src/alphalens/extra.py` and
      the coverage in `tests/test_extra.py`.

## Documentation

- [ ] None

