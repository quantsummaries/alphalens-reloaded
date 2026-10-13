# Alphalens Reloaded — Maintenance TODO

This file tracks **work to do on the codebase itself**: bugs, missing tests,
stale docs, upstream features to port, performance fixes.

The **learning roadmap** (for someone coming to the codebase fresh) lives in
[`CODE_LEARN.md`](CODE_LEARN.md). Project-wide conventions:
[`../PROJECT-CONVENTIONS.md`](../PROJECT-CONVENTIONS.md).

## Bugs / behavior fixes

- [ ] `tears.create_information_tear_sheet(..., return_df=True)` still
      returns a figure handle because `plot_information_table(...,
      as_figure=True)` is hard-coded at `src/alphalens/tears.py:420`. Honor
      `return_df` by threading it through.
- [ ] `tears.create_turnover_tear_sheet(..., return_df=True)` calls
      `plot_turnover_table(..., return_df=return_df)` at
      `src/alphalens/tears.py:558` but discards the result; return the
      tables to the caller.

## Test coverage gaps

- [ ] Promote `tests/test_wrapper.py` (currently script-style helpers only,
      `pytest tests/test_wrapper.py` collects 0 items) into real `test_*`
      functions covering `return_analysis_wrapper`,
      `information_analysis_wrapper`, `turnover_analysis_wrapper`,
      `full_tear_sheet_wrapper`, including the save-file path.
- [ ] Validate the `hit_rate` calculation in `src/alphalens/extra.py` and
      the coverage in `tests/test_extra.py`.

## Documentation

- [ ] Commit the staged pdoc regeneration under `docs/pdoc/alphalens/`
      (new `extra.html`, modified `index/performance/plotting/tears/utils/wrapper.html`).
- [ ] Commit staged changes to `src/alphalens/wrapper.py` and `docs/utils.md`.

## Upstream alignment / features to port

- [ ]

## Performance

- [ ]
