# Additional notes on `long_short`, `group_neutral`, and `by_group`

This note summarizes how the high-level tear-sheet arguments `long_short`, `group_neutral`, and `by_group` are used across the codebase.

## Table of contents

- [Quick mapping](#quick-mapping)
- [Clarification: what gets demeaned?](#clarification-what-gets-demeaned)
- [Function-by-function usage of `long_short`](#function-by-function-usage-of-long_short)
  - [Practical interpretation of `long_short`](#practical-interpretation-of-long_short)
- [Function-by-function usage of `group_neutral`](#function-by-function-usage-of-group_neutral)
  - [Practical interpretation of `group_neutral`](#practical-interpretation-of-group_neutral)
- [Function-by-function usage of `by_group`](#function-by-function-usage-of-by_group)
  - [Practical interpretation of `by_group`](#practical-interpretation-of-by_group)

---

## Quick mapping

At the public API level:

- `long_short` is the user-facing name for the lower-level flag `demeaned`
- `group_neutral` is the user-facing name for the lower-level flag `group_adjust`

These two flags are related, but they are not the same:

- `long_short` asks whether the analysis should use a demeaned, dollar-neutral long/short interpretation.
- `group_neutral` asks whether group effects should be neutralized so that groups contribute equally or returns are demeaned within groups.

They are independent flags in the API, so all four combinations are valid.

---

## Clarification: what gets demeaned?

There are two separate questions in this codebase:

1. **What object is being demeaned?**
   - **forward returns**, or
   - **factor values**

2. **At what level is the demeaning done?**
   - across the **full universe**, or
   - within each **group**

The flags `long_short` and `group_neutral` mainly answer the **second** question:

- `long_short` corresponds to **universe-level** demeaning
- `group_neutral` corresponds to **group-level** demeaning / neutralization

Which object gets demeaned depends on the function:

| Flag | Forward-return use case | Factor-value use case |
|---|---|---|
| `long_short=True` | demean forward returns across the universe | demean factor values across the universe |
| `group_neutral=True` | demean forward returns within each group | demean factor values within each group, or more generally build group-neutral weights |

So neither flag is tied to only one object. Depending on the function being called, the same flag can apply either to **forward returns** or to **factor values**.

---

## Function-by-function usage of `long_short`

| Function | Internal mapping | What `True` changes | What `False` means |
|---|---|---|---|
| `tears.create_summary_tear_sheet(...)` | passed as `demeaned=long_short` and to `factor_alpha_beta(...)` | Mean quantile returns are demeaned across the factor universe; alpha/beta are based on long/short-style factor returns | Summary uses non-demeaned return statistics |
| `tears.create_returns_tear_sheet(...)` | passed to `factor_returns(...)`; also passed as `demeaned=long_short` and into `factor_alpha_beta(...)` | Factor return series uses long/short-style weights; quantile-return summaries use demeaned forward returns | Return tear sheet uses non-demeaned weighting and raw forward-return summaries |
| `tears.create_event_returns_tear_sheet(...)` | passed into event/cumulative return analysis | Event-study cumulative-return summaries are computed on a demeaned basis | Event-study summaries use non-demeaned returns |
| `wrapper.return_analysis_wrapper(...)` | passed as `demeaned=long_short` | Wrapper computes long/short-style mean return by quantile statistics | Wrapper computes non-demeaned mean return by quantile statistics |
| `wrapper.full_tear_sheet_wrapper(...)` | forwarded to `return_analysis_wrapper(...)` as `long_short` | Full-wrapper return analysis uses long/short-style demeaning/weighting where applicable | Full-wrapper return analysis uses non-demeaned behavior |
| `performance.factor_cumulative_returns(...)` | passed to `factor_returns(...)` | Simulates cumulative returns of a long/short factor portfolio | Simulates cumulative returns of a non-demeaned factor portfolio |
| `performance.factor_positions(...)` | passed to `factor_weights(...)` | Builds positions from long/short-style weights | Builds positions from non-demeaned weights |
| `performance.create_pyfolio_input(...)` | passed to `factor_cumulative_returns(...)` and `factor_positions(...)` | Returns and positions are prepared for a long/short strategy | Returns and positions are prepared for a non-demeaned strategy |
| `performance.factor_returns(...)` | receives the mapped flag as `demeaned` | Uses long/short-style weights produced by `factor_weights(...)` | Uses raw factor-weighted exposure without demeaning first |
| `performance.factor_weights(...)` | uses `demeaned` directly | Demeans factor values before scaling weights, creating a dollar-neutral long/short weighting scheme | Uses raw factor values when building weights |
| `performance.mean_return_by_quantile(...)` | receives the mapped flag as `demeaned` | Demeans forward returns before averaging by quantile | Uses forward returns as-is when computing quantile averages |
| `performance.factor_alpha_beta(...)` | receives the mapped flag as `demeaned` | Alpha/beta are computed from long/short-style factor returns | Alpha/beta are computed from non-demeaned factor returns |
| `performance.average_cumulative_return_by_quantile(...)` | receives the mapped flag as `demeaned` | Average cumulative return by quantile is computed on a demeaned basis | Average cumulative return by quantile is computed without demeaning |

### Practical interpretation of `long_short`

`long_short=True` does not always act on the same object internally:

- in portfolio-construction functions such as `factor_weights(...)`, `factor_returns(...)`, and `factor_positions(...)`, it changes how **weights** are built;
- in summary functions such as `mean_return_by_quantile(...)`, it changes whether **forward returns** are demeaned before summary statistics are computed.

So the intent is consistent, but the implementation target differs by function.

---

## Function-by-function usage of `group_neutral`

| Function | Internal mapping | What `True` changes | What `False` means |
|---|---|---|---|
| `tears.create_summary_tear_sheet(...)` | passed as `group_adjust=group_neutral` and to `factor_alpha_beta(...)` | Mean quantile returns are demeaned within each group; alpha/beta are based on group-neutral factor returns | Summary ignores group balancing and group-level return demeaning |
| `tears.create_returns_tear_sheet(...)` | passed to `factor_returns(...)`; also passed as `group_adjust=group_neutral` and into `factor_alpha_beta(...)` | Factor return series uses group-neutral weights; quantile-return summaries use forward returns demeaned within groups; cumulative-return title/interpretation becomes group-neutral | Return tear sheet does not impose group-neutral weighting or group-wise return demeaning |
| `tears.create_information_tear_sheet(...)` | passed as `group_adjust=group_neutral` to IC functions | Forward returns are demeaned within groups before IC computation, removing group-level return effects from the IC | IC is computed without group-wise demeaning |
| `tears.create_event_returns_tear_sheet(...)` | passed into cumulative return analysis | Event-study cumulative returns are neutralized at the group level | Event-study cumulative returns are not neutralized at the group level |
| `wrapper.return_analysis_wrapper(...)` | passed as `group_adjust=group_neutral` | Wrapper computes group-neutral return statistics | Wrapper computes non-group-neutral return statistics |
| `wrapper.full_tear_sheet_wrapper(...)` | forwarded to `information_analysis_wrapper(...)` and `return_analysis_wrapper(...)` as `group_neutral` | Full-wrapper IC and return analysis use group-level demeaning/neutralization behavior | Full-wrapper IC and return analysis use non-group-neutral behavior |
| `wrapper.information_analysis_wrapper(...)` | passed as `group_adjust=group_neutral` | Wrapper computes group-neutral IC statistics | Wrapper computes non-group-neutral IC statistics |
| `performance.factor_cumulative_returns(...)` | passed to `factor_returns(...)` | Simulates cumulative returns of a group-neutral factor portfolio | Simulates cumulative returns without group balancing |
| `performance.factor_positions(...)` | passed to `factor_weights(...)` | Builds positions so groups contribute equally | Builds positions without group balancing |
| `performance.create_pyfolio_input(...)` | passed to `factor_cumulative_returns(...)` and `factor_positions(...)` | Returns and positions are prepared for a group-neutral strategy | Returns and positions are prepared without group-neutral construction |
| `performance.factor_information_coefficient(...)` | receives the mapped flag as `group_adjust` | Demeans forward returns by group before computing IC | Uses forward returns without group-level demeaning |
| `performance.mean_information_coefficient(...)` | receives the mapped flag as `group_adjust` | Computes average IC from group-neutral IC inputs | Computes average IC from non-group-neutral IC inputs |
| `performance.factor_weights(...)` | receives the mapped flag as `group_adjust` | Computes weights within each group first, then rebalances so each group has equal weight; if `demeaned=True`, factor demeaning occurs at the group level | Ignores group labels in weight construction |
| `performance.factor_returns(...)` | receives the mapped flag as `group_adjust` | Uses group-neutral weights produced by `factor_weights(...)` | Uses non-group-neutral weights |
| `performance.mean_return_by_quantile(...)` | receives the mapped flag as `group_adjust` | Demeans forward returns within each group before averaging by quantile | Uses either universe-wide demeaning or no demeaning, depending on `demeaned` |
| `performance.factor_alpha_beta(...)` | receives the mapped flag as `group_adjust` | Alpha/beta are computed from group-neutral factor returns | Alpha/beta are computed from non-group-neutral factor returns |
| `performance.average_cumulative_return_by_quantile(...)` | receives the mapped flag as `group_adjust` | Average cumulative return by quantile is neutralized at the group level | Average cumulative return by quantile is not group-neutral |

### Practical interpretation of `group_neutral`

`group_neutral=True` affects two kinds of computations in this project:

1. **Forward-return demeaning by group**
   - Example: `factor_information_coefficient(...)` and `mean_return_by_quantile(...)`
   - Here the forward returns are adjusted within each group before statistics are computed.

2. **Portfolio weight construction with equal group contribution**
   - Example: `factor_weights(...)`, `factor_returns(...)`, `factor_positions(...)`
   - Here the portfolio is built so that groups contribute equally; if `long_short=True`, the factor-value demeaning happens at the group level.

So, unlike `by_group`, which mainly changes how results are broken out and displayed, `group_neutral` changes the actual calculations.

**Precedence detail:** in `mean_return_by_quantile(...)`, when `group_adjust=True` (mapped from `group_neutral=True`), group-level forward-return demeaning is applied and the universe-level demeaning path controlled by `demeaned`/`long_short` is not used for that step.

---

## Function-by-function usage of `by_group`

| Function | Internal mapping | What `True` changes | What `False` means |
|---|---|---|---|
| `tears.create_returns_tear_sheet(...)` | passed as `by_group=by_group` to `mean_return_by_quantile(...)` for the group breakout section | Adds a separate quantile-return analysis and bar plots for each group | Shows only pooled quantile-return charts |
| `tears.create_information_tear_sheet(...)` | passed as `by_group=by_group` to IC functions and group-level IC plotting | Computes and displays IC statistics separately for each group | Computes and displays only pooled IC results |
| `tears.create_full_tear_sheet(...)` | forwarded to underlying return and information tear-sheet helpers | Full tear sheet includes the per-group breakout views where supported | Full tear sheet keeps the pooled views only |
| `tears.create_event_returns_tear_sheet(...)` | passed as `by_group=by_group` to `average_cumulative_return_by_quantile(...)` | Computes cumulative return by quantile separately for each group | Computes cumulative return by quantile on the pooled universe |
| `wrapper.return_analysis_wrapper(...)` | passed directly as `by_group=by_group` to `mean_return_by_quantile(...)` and return tear-sheet generation | Wrapper can compute mean return by quantile separately per group | Wrapper computes only pooled quantile-return statistics |
| `wrapper.information_analysis_wrapper(...)` | passed directly as `by_group=by_group` to IC functions and information tear-sheet generation | Wrapper can compute IC separately per group | Wrapper computes only pooled IC statistics |
| `wrapper.full_tear_sheet_wrapper(...)` | forwarded to `information_analysis_wrapper(...)` and `return_analysis_wrapper(...)` as `by_group` | Full-wrapper IC and return outputs can be broken out per group where supported | Full-wrapper IC and return outputs stay pooled |
| `performance.factor_information_coefficient(...)` | uses `by_group` directly in the `groupby(...)` grouper | Adds `group` to the grouping keys so IC is computed separately by date and group | Computes IC only by date across the full universe |
| `performance.mean_information_coefficient(...)` | uses `by_group` directly in the aggregation grouper | Keeps separate mean IC values for each group | Collapses IC into a single pooled mean |
| `performance.mean_return_by_quantile(...)` | uses `by_group` directly in the aggregation grouper | Adds `group` to the grouping keys so quantile return statistics are computed separately for each group | Computes quantile return statistics across the pooled universe |
| `performance.average_cumulative_return_by_quantile(...)` | uses `by_group` directly to branch into per-group processing | Iterates over groups and returns cumulative-return summaries with an added `group` index level | Computes one pooled cumulative-return summary |

### Practical interpretation of `by_group`

`by_group=True` mainly changes how results are **segmented and reported by group**.

It can affect more than plotting, because lower-level functions such as `mean_return_by_quantile(...)`, `factor_information_coefficient(...)`, and `average_cumulative_return_by_quantile(...)` actually change their aggregation keys and return shapes when `by_group=True`. In practice, though, the purpose is still to obtain **separate per-group outputs** rather than to neutralize or reweight the analysis.

So the three flags can be summarized as follows:

- `long_short`: switch to a demeaned, long/short interpretation
- `group_neutral`: neutralize group effects in the calculations
- `by_group`: break out the results separately for each group
