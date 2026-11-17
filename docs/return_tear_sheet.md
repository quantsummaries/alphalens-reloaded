# Return tear sheet

## Table of contents

- [1. Returns Analysis table](#1-returns-analysis-table)
  - [1.1 Calculate the aggregate portfolio's return series](#11-calculate-the-aggregate-portfolios-return-series)
  - [1.2 Calculate alpha, beta, and their t-statistics](#12-calculate-alpha-beta-and-their-t-statistics)
  - [1.3 Assemble and render the seven-row table](#13-assemble-and-render-the-seven-row-table)
- [2. Mean Period Wise Return By Factor Quantile](#2-mean-period-wise-return-by-factor-quantile)
  - [2.1 Function that generates the chart](#21-function-that-generates-the-chart)
  - [2.2 Stock weights behind each bar](#22-stock-weights-behind-each-bar)
- [3. Equal Weighted Long/Short Portfolio Cumulative Return (1D Period)](#3-equal-weighted-longshort-portfolio-cumulative-return-1d-period)
  - [3.1 Construct the portfolio return series](#31-construct-the-portfolio-return-series)
  - [3.2 Compound and plot the period returns](#32-compound-and-plot-the-period-returns)
  - [3.3 Comment: cumulative return versus annualized alpha](#33-comment-cumulative-return-versus-annualized-alpha)
- [4. Cumulative Return by Quantile](#4-cumulative-return-by-quantile)
  - [4.1 Calculate each quintile's date-level returns](#41-calculate-each-quintiles-date-level-returns)
  - [4.2 Compound and plot the five return series](#42-compound-and-plot-the-five-return-series)
  - [4.3 Comment: relationship to the mean-return bars in section 2](#43-comment-relationship-to-the-mean-return-bars-in-section-2)
- [5. Top Minus Bottom Quantile Mean Return](#5-top-minus-bottom-quantile-mean-return)
  - [5.1 Calculate the date-level quintile returns and standard errors](#51-calculate-the-date-level-quintile-returns-and-standard-errors)
  - [5.2 Calculate the top-minus-bottom spread](#52-calculate-the-top-minus-bottom-spread)
  - [5.3 Plot the spread, moving average, and error band](#53-plot-the-spread-moving-average-and-error-band)
  - [5.4 Relationship to the table and the other return plots](#54-relationship-to-the-table-and-the-other-return-plots)

## 1. Returns Analysis table

| Metric | 1D |
| --- | ---: |
| Ann. alpha | 0.016 |
| t-stat(alpha) | 4.141 |
| beta | 0.064 |
| t-stat(beta) | 0.352 |
| Mean Period Wise Return Top Quantile (bps) | 1.222 |
| Mean Period Wise Return Bottom Quantile (bps) | -1.121 |
| Mean Period Wise Spread (bps, 100% gross) | 1.171 |

Values transcribed from
`~/tmp/hazeltree/baseline/ic_analysis/Equity_LS/1D/rtrn_tear_sheet_net_buy_mv_of_adv.png`.
The displayed values are rounded to three decimal places. In this project,
`1D` denotes the return from 10:00 on one trading day to 10:00 on the next.

The table is assembled and displayed by `alphalens.plotting.plot_returns_table()`.
Its numbers come from earlier calculations inside
`alphalens.tears.create_returns_tear_sheet()`, reached through
`full_tear_sheet_wrapper()` in [04_ic_analysis.py](../scripts/04_ic_analysis.py).

The first four rows describe the **aggregate, median-split equal-weight
portfolio**. The last three describe the **highest and lowest quintiles and
their spread**. These are separate portfolio constructions.

[Back to TOC](#table-of-contents)

### 1.1 Calculate the aggregate portfolio's return series

For this feature and horizon, the effective call, written with named arguments, is:

```python
portfolio_returns = performance.factor_returns(
    factor_data=clean_data,
    demeaned=True,
    group_adjust=False,
    equal_weight=True,
)
```

| Argument | Meaning and effect |
| --- | --- |
| `factor_data=clean_data` | Cleaned observations indexed by `(date, asset)`, containing `factor`—here, `net_buy_mv_of_adv`—the stock's `1D` residual return, and its quantile label. Determines which stocks and dates enter the analysis. |
| `demeaned=True` | Requests long/short weight construction. Together with `equal_weight=True`, splits stocks above and below each date's cross-sectional median factor value. Stocks exactly at the median receive zero weight. |
| `group_adjust=False` | Constructs weights across the whole cleaned cross-section, without separate group allocations. |
| `equal_weight=True` | Assigns equal weights within each populated leg. When both legs are populated, long weights total +0.5 and short weights total -0.5, for 100% gross exposure. |

Factor magnitudes determine which side of the median a stock occupies, but do
not determine its weight within that side. If median ties leave only one leg
populated, Alphalens assigns that leg 100% gross exposure. If all factor values
are identical and survive cleaning, the weights are zero.

The function calculates one portfolio return per analyzed date:

```text
R_portfolio[t] = sum_i(weight[i, t] * stock_forward_return[i, t])
```

These returns supply the regression below. Quintile labels do not determine
this aggregate portfolio's weights. In particular, this is not a portfolio
restricted to the highest and lowest quintiles.

[Back to TOC](#table-of-contents)

### 1.2 Calculate alpha, beta, and their t-statistics

The effective call is:

```python
alpha_beta = performance.factor_alpha_beta(
    factor_data=clean_data,
    returns=portfolio_returns,
    demeaned=True,
    group_adjust=False,
    periods_per_year=252,
)
```

This fits a time-series OLS regression with one observation per analyzed date:

```text
R_portfolio[t] = a + beta * R_universe[t] + error[t]
```

| Argument | Meaning and effect |
| --- | --- |
| `factor_data` | Supplies the regression benchmark: the equal-weight mean `1D` residual return across all stocks in the cleaned universe on each date. This is not an external market index. |
| `returns` | Supplies the dependent variable: the portfolio return series calculated in section 1.1. Changing this series changes the fitted coefficients and t-statistics. |
| `demeaned=True` | Does not reconstruct or modify the supplied returns. It would affect portfolio construction if `returns=None`. |
| `group_adjust=False` | Also does not reconstruct supplied returns. The regression benchmark remains the pooled universe mean. |
| `periods_per_year=252` | Converts the fitted per-period intercept into annualized alpha using `(1 + a)**252 - 1`. Affects annualized alpha only, not beta or either t-statistic. |

The `equal_weight` argument is omitted from this particular call and defaults
to `False`. That does not undo equal weighting: `factor_alpha_beta()` uses the
already-computed `portfolio_returns` directly. Its weighting arguments are used
only when it must construct returns itself because `returns=None`.

The four output rows have these meanings:

| Row | Interpretation |
| --- | --- |
| `Ann. alpha` | The fitted intercept `a`, compounded over 252 periods. The intercept is the portfolio's fitted one-period return when the universe-average residual return is zero. The displayed `0.016` is approximately 1.6% annualized alpha, not the portfolio's realized compound annual growth rate. |
| `t-stat(alpha)` | `a / SE_OLS(a)`, testing the per-period intercept against zero. The displayed value is `4.141`. It is not calculated from the annualized alpha. |
| `beta` | The fitted slope on the universe-average residual return. The displayed `0.064` means a 1-basis-point increase in the benchmark corresponds to a 0.064-basis-point increase in the fitted portfolio return, holding the intercept fixed. |
| `t-stat(beta)` | `beta / SE_OLS(beta)`, testing the slope against zero. The displayed value is `0.352`. |

The t-statistics use conventional OLS standard errors. They are not annualized
and are not adjusted for heteroskedasticity or serial correlation. They are
separate from the Newey–West-adjusted statistics in the IC tear sheet.

[Back to TOC](#table-of-contents)

### 1.3 Assemble and render the seven-row table

The rendering call is:

```python
rtrns_tbl = plotting.plot_returns_table(
    alpha_beta,
    mean_quant_rateret,
    mean_ret_spread_quant,
    tables_as_figures=True,
    ax=gf.next_row(),
)
```

| Argument | Effect on the table |
| --- | --- |
| `alpha_beta` | Supplies the first four regression rows. Annualized alpha is expressed as a decimal return; beta and both t-statistics are dimensionless. |
| `mean_quant_rateret` | Supplies mean returns for all five quintiles. The renderer selects the highest and lowest quintiles and multiplies their returns by 10,000 to express them in basis points: `1.222` and `-1.121` here. |
| `mean_ret_spread_quant` | Supplies each date's 50%-long-Q5/50%-short-Q1 spread. The renderer averages it across dates and converts it to basis points, producing `1.171` here. |
| `tables_as_figures=True` | Renders a graphical table. Does not change the calculated values. With `False`, the function displays a text table instead and still returns the table data. |
| `ax` | Selects where the table appears in the tear-sheet figure. Does not change its values. `gf.next_row()` allocates the next row of the figure layout. |

For `net_buy_mv_of_adv`, stage 04 passes `quantiles=5, bins=None`, requesting
five approximately equal-count buckets on each date. Within each bucket,
stocks contribute equally to the bucket's average return. Because
`long_short=True`, the universe-average stock return is subtracted first:

```text
R_quintile[q, t] = mean(stock_returns in quintile q on date t)
                  - mean(stock_returns in the cleaned universe on date t)
```

`performance.mean_return_by_quantile(..., by_date=False, demeaned=True,
group_adjust=False)` averages these date-level bucket returns across dates,
giving each available date equal weight. The tear sheet converts each horizon
to the first return column's base period before display. This image contains
only `1D`, so that conversion leaves the returns unchanged.

The spread is calculated from the date-level bucket returns:

```text
spread[t] = 0.5 * (R_quintile[5, t] - R_quintile[1, t])
```

The factor of 0.5 gives 100% gross exposure: 50% long and 50% short. The
displayed spread is therefore approximately `(1.222 - (-1.121)) / 2`, with
the calculation performed using unrounded values. It is an average return
per `1D` holding period, before transaction costs, rather than an annualized
return. Missing buckets on some dates can also make the spread's averaging
sample differ from either bucket's individual mean-return sample.

[Back to TOC](#table-of-contents)

## 2. Mean Period Wise Return By Factor Quantile

![Mean Period Wise Return By Factor Quantile for net_buy_mv_of_adv, Equity LS, 1D returns][plot-mean-period-wise-return]

*Equity LS, net_buy_mv_of_adv, 1D. Reproduced from the baseline analysis data using the tear sheet's Alphalens calculation.*

[Back to TOC](#table-of-contents)

### 2.1 Function that generates the chart

This bar chart is generated by
`alphalens.plotting.plot_quantile_returns_bar()`, called inside
`create_returns_tear_sheet()`:

```python
plotting.plot_quantile_returns_bar(
    mean_quant_rateret,
    by_group=False,
    ylim_percentiles=None,
    ax=gf.next_row(),
)
```

| Argument | Effect |
| --- | --- |
| `mean_quant_rateret` | Supplies the mean return for each quintile and forward-return horizon as decimal returns. The plotting function converts them to basis points for the bars. |
| `by_group=False` | Produces one pooled chart instead of separate charts for each group. |
| `ylim_percentiles=None` | Uses the data range for the vertical axis rather than restricting it to selected percentiles. |
| `ax=gf.next_row()` | Places the chart in the next row of the tear-sheet layout. Does not change the values. |

The plotting function does not calculate portfolio weights. Its input is
calculated earlier:

```python
mean_quant_ret, _ = performance.mean_return_by_quantile(
    factor_data,
    by_date=False,
    by_group=False,
    demeaned=True,       # because long_short=True
    group_adjust=False,
)

mean_quant_rateret = mean_quant_ret.apply(
    utils.rate_of_return,
    axis=0,
    base_period=mean_quant_ret.columns[0],
)
```

`by_date=False` requests one mean per quintile over the analysis period.
The function first calculates a return for each date and quintile, then
averages those returns across dates. `group_adjust=False` uses the entire
cleaned universe for return demeaning. For this single `1D` horizon, the
`rate_of_return` conversion leaves the returns unchanged.

[Back to TOC](#table-of-contents)

### 2.2 Stock weights behind each bar

For each analyzed date, stocks are assigned to five quintiles according to
their factor values. Each stock inside a selected quintile contributes the
same positive weight to that bucket's average return:

```text
bucket weight[i, t] = 1 / N_quintile[q, t]
```

Factor values determine bucket membership, not position size within the
bucket. The highest quintile contains approximately the highest 20% of
stocks, and the lowest contains approximately the lowest 20%.

Because the call uses `demeaned=True`, Alphalens first subtracts the cleaned
universe's mean forward return from each stock's forward return. The
date-level return for quintile `q` is therefore:

```text
R_quintile[q, t] = sum(returns of stocks in quintile q) / N_quintile[q, t]
                  - sum(returns of stocks in the universe) / N_universe[t]
```

After this universe adjustment, the calculation is equivalent to the
following net stock weights:

| Stock membership | Effective weight |
| --- | --- |
| Inside the selected quintile | `1 / N_quintile[q, t] - 1 / N_universe[t]` |
| Outside the selected quintile | `-1 / N_universe[t]` |

All five quintiles use the same calculation, including the lowest quintile.
The lowest quintile is not automatically assigned negative bucket weights;
its negative bar means its average return underperformed the universe
average over the sample.

Finally, each bar is the arithmetic average of that quintile's date-level
adjusted returns, converted to basis points:

```text
bar_height[q] = 10000 * mean_over_available_dates(R_quintile[q, t])
```

Each available date receives equal weight, even when the number of stocks
changes across dates. These bucket returns are not additionally normalized
to 100% gross exposure; the 0.5 scaling applies to the separate top-minus-bottom
spread in section 1.

The `equal_weight=True` argument controls the separate aggregate portfolio
used for alpha, beta, and the single portfolio cumulative-return chart. It
does not change this bar chart's calculation: the bucket averages already
use equal stock weights. There is no median split within a quintile.

[Back to TOC](#table-of-contents)

## 3. Equal Weighted Long/Short Portfolio Cumulative Return (1D Period)

![Equal Weighted Long/Short Portfolio Cumulative Return for net_buy_mv_of_adv, Equity LS, 1D returns][plot-equal-weighted-cumulative-return]

*Equity LS, net_buy_mv_of_adv, 1D. Reproduced from the baseline analysis data using the tear sheet's Alphalens calculation.*

[Back to TOC](#table-of-contents)

### 3.1 Construct the portfolio return series

The period-by-period portfolio returns are constructed by
`alphalens.performance.factor_returns()`:

```python
portfolio_returns = performance.factor_returns(
    factor_data,
    demeaned=True,       # long_short=True
    group_adjust=False,  # group_neutral=False
    equal_weight=True,
)
```

`factor_data` is the cleaned `(date, asset)` panel for `net_buy_mv_of_adv` and
the `1D` return horizon. The cleaning step uses `quantiles=5, bins=None`, but
the resulting quintile labels do not determine this portfolio's weights.

Internally, `factor_returns()` calls `performance.factor_weights()` to assign
weights on each analyzed date:

- `demeaned=True` together with `equal_weight=True` splits stocks above and
  below the cross-sectional median factor value.
- Stocks above the median receive equal positive weights; stocks below the
  median receive equal negative weights. Stocks exactly at the median
  receive zero weight.
- `group_adjust=False` applies this calculation across the entire cleaned
  cross-section, without separate group allocations.

When both legs are populated, the weights are:

| Stock's factor value | Portfolio weight |
| --- | --- |
| Above the median | `+0.5 / N_long[t]` |
| Below the median | `-0.5 / N_short[t]` |
| Equal to the median | `0` |

Long weights therefore total +0.5 and short weights total -0.5: 100% gross
exposure and zero net exposure. Median ties can leave different numbers of
stocks in the two legs, so equal weights within a leg need not have the same
absolute size as weights in the other leg. If only one leg is populated,
Alphalens gives that leg 100% gross exposure. A constant factor produces
zero weights if its observations survive cleaning.

The function applies those weights directly to the supplied stock residual
returns and sums across stocks:

```text
R_portfolio[t] = sum_i(weight[i, t] * stock_forward_return[i, t])
```

There is no separate subtraction of the universe-average return in this
calculation. Here, `demeaned=True` controls factor-to-weight construction;
section 2's bucket-return calculation uses return demeaning instead.

This is the same aggregate portfolio return series used to estimate alpha,
beta, and their t-statistics in section 1. It is not restricted to the top
and bottom quintiles.

[Back to TOC](#table-of-contents)

### 3.2 Compound and plot the period returns

The chart is drawn by `alphalens.plotting.plot_cumulative_returns()`:

```python
plotting.plot_cumulative_returns(
    portfolio_returns["1D"],
    period="1D",
    title="Equal Weighted Long/Short Portfolio Cumulative Return (1D Period)",
    ax=gf.next_row(),
)
```

| Argument | Effect |
| --- | --- |
| `portfolio_returns["1D"]` | Supplies the one-period portfolio return series calculated in section 3.1. These are decimal returns, not basis points. |
| `period="1D"` | Identifies the return horizon for labeling. The function compounds observations directly; this argument does not resample the data or annualize returns. |
| `title` | Supplies the chart title identifying equal-weight long/short construction and the holding period. |
| `ax=gf.next_row()` | Places the chart in the next row of the tear-sheet layout. Does not change the values. |

The plotting function calls `performance.cumulative_returns()`, which
delegates to `empyrical.cum_returns(..., starting_value=1)`:

```text
V[t] = product_over_periods_up_to_t(1 + R_portfolio[period])
```

The line is a wealth index based on an initial value of 1. For example, a
value of 1.10 represents a cumulative gain of 10%. The horizontal line at 1
marks zero cumulative gain. This is compounding, rather than an arithmetic
sum of period returns, and is not an annualized return.

For this `1D` analysis, stage 04 samples every available session. Each return
covers 10:00 to 10:00 on the next trading day. The plotting function does not
remove overlapping holding periods; the sampling schedule is established
before returns are passed to it.

[Back to TOC](#table-of-contents)

### 3.3 Comment: cumulative return versus annualized alpha

The cumulative-return curve and `Ann. alpha` in the Returns Analysis table
use the same aggregate portfolio return series, but measure different things.

The curve compounds the portfolio's actual period returns:

```text
V[T] = product_over_periods_up_to_T(1 + R_portfolio[t])
```

Its ending value of approximately `1.0983` represents a cumulative gain of
approximately 9.83% over the whole sample.

Annualized alpha is calculated by regressing those same portfolio returns
on the universe-average return:

```text
R_portfolio[t] = a + beta * R_universe[t] + error[t]
Ann. alpha = (1 + a)**252 - 1
```

The table's approximately 1.6% annualized alpha therefore measures the
annualized regression intercept. It is not the cumulative curve's total gain
or its annualized growth rate.

Annualizing the cumulative curve would produce the portfolio's compound
annual growth rate (CAGR), which generally differs from annualized alpha.

[Back to TOC](#table-of-contents)

## 4. Cumulative Return by Quantile

![Cumulative Return by Quantile for net_buy_mv_of_adv, Equity LS, 1D returns, with five quintile curves][plot-cumulative-return-by-quantile]

*Equity LS, net_buy_mv_of_adv, 1D. Reproduced from the baseline analysis data using the tear sheet's Alphalens calculation.*

[Back to TOC](#table-of-contents)

### 4.1 Calculate each quintile's date-level returns

`performance.mean_return_by_quantile()` calculates each quintile's return
on each analyzed date:

```python
mean_quant_ret_bydate, _ = performance.mean_return_by_quantile(
    factor_data,
    by_date=True,
    by_group=False,
    demeaned=True,       # long_short=True
    group_adjust=False,
)
```

| Argument | Effect |
| --- | --- |
| `factor_data` | Supplies the cleaned stock forward returns and the quintile membership determined from `net_buy_mv_of_adv` on each date. |
| `by_date=True` | Retains a separate return for each date and quintile, rather than averaging across dates. These observations are needed for compounding. |
| `by_group=False` | Computes returns per quintile and date without a separate group breakdown. |
| `demeaned=True` | Subtracts each date's cleaned-universe mean forward return from each stock's forward return before calculating bucket averages. |
| `group_adjust=False` | Uses the pooled universe for return demeaning, without separate within-group benchmarks. |

For each quintile `q` and date `t`, the return is:

```text
R_quintile[q, t] = equal_weight_mean_return_of_stocks_in_quintile[q, t]
                  - equal_weight_mean_return_of_cleaned_universe[t]
```

The stock-weighting calculation is the same as in section 2: stocks inside
each bucket contribute equally to its average, and the universe average is
subtracted. There is no median split within the bucket. The lowest-quintile
return is used directly; its sign is not reversed to represent shorting that
bucket.

[Back to TOC](#table-of-contents)

### 4.2 Compound and plot the five return series

`plotting.plot_cumulative_returns_by_quantile()` generates the chart:

```python
plotting.plot_cumulative_returns_by_quantile(
    mean_quant_ret_bydate["1D"],
    period="1D",
    ax=gf.next_row(),
)
```

| Argument | Effect |
| --- | --- |
| `mean_quant_ret_bydate["1D"]` | Supplies the date-level `1D` return for each quintile as decimal returns. The series is indexed by quintile and date. |
| `period="1D"` | Supplies the horizon label in the chart title. Observations are compounded directly; this argument does not annualize returns or remove overlapping holding periods. |
| `ax=gf.next_row()` | Places the chart in the next row of the tear-sheet layout. Does not change its values. |

Internally, the plotting function rearranges the data into five columns,
one for each quintile, and compounds each column independently:

```python
ret_wide = quantile_returns.unstack("factor_quantile")
cum_ret = ret_wide.apply(performance.cumulative_returns)
```

`performance.cumulative_returns()` delegates to:

```python
empyrical.cum_returns(returns, starting_value=1)
```

Each curve therefore represents a wealth index:

```text
V_quintile[q, t] = product_over_dates_up_to_t(1 + R_quintile[q, date])
```

The initial wealth is 1. A value above 1 indicates a positive compounded
result from the universe-adjusted bucket returns; a value below 1 indicates
a negative compounded result. The plotting function orders the legend from
Q5 to Q1 and colors the curves accordingly.

Although the axis is labeled "Log Cumulative Returns", its displayed values
are wealth indices. The function uses a `symlog` axis scale; it does not
replace the plotted values with logarithms of wealth.

The separate median-split aggregate portfolio and its `equal_weight=True`
setting do not determine these five curves. The quintile returns already
use equal weights within each bucket.

[Back to TOC](#table-of-contents)

### 4.3 Comment: relationship to the mean-return bars in section 2

The two plots use the same date-level quintile returns, but summarize them
differently:

| Plot | Calculation for quintile `q` | Interpretation |
| --- | --- | --- |
| Mean Period Wise Return By Factor Quantile (section 2) | `10000 * mean_over_available_dates(R_quintile[q, t])` | Arithmetic average return per `1D` holding period, in basis points. |
| Cumulative Return by Quantile (this section) | `product_over_dates_up_to_t(1 + R_quintile[q, date])` | Compounded wealth through time, based on an initial value of 1. |

For example, Q5's bar of approximately 1.222 bps is the arithmetic average
of the period returns compounded into the Q5 curve.

The code reflects the distinction:

```python
# Section 2: average the date-level bucket returns across dates.
performance.mean_return_by_quantile(..., by_date=False)

# Section 4: retain the date-level bucket returns for compounding.
performance.mean_return_by_quantile(..., by_date=True)
```

For this single `1D` horizon, the base-period conversion applied before
plotting the bars leaves the mean returns unchanged, so both plots use the
same underlying return definition.

The arithmetic mean alone does not determine a curve's final wealth because
compounding also depends on the variability of period returns. For example,
returns of +10% and -10% have an arithmetic mean of zero, but compound to:

```text
1.10 * 0.90 = 0.99
```

Thus, a zero mean return can coexist with a cumulative loss. The bars
summarize average one-period performance, while the curves show the
compounded result and when gains and drawdowns occurred.

[Back to TOC](#table-of-contents)

## 5. Top Minus Bottom Quantile Mean Return

![Top Minus Bottom Quantile Mean Return at 100% gross exposure for net_buy_mv_of_adv, Equity LS, 1D returns][plot-top-minus-bottom-spread]

*Equity LS, net_buy_mv_of_adv, 1D. Reproduced from the baseline analysis data using the tear sheet's Alphalens calculation.*

This plot shows the date-by-date return of a portfolio that is 50% long the
highest quintile and 50% short the lowest quintile, at 100% gross exposure.
It shows individual holding-period returns, not a cumulative-return curve.

[Back to TOC](#table-of-contents)

### 5.1 Calculate the date-level quintile returns and standard errors

The calculation starts with the same date-level quintile returns used in
section 4, together with their cross-sectional standard errors:

```python
mean_quant_ret_bydate, std_quant_daily = performance.mean_return_by_quantile(
    factor_data,
    by_date=True,
    by_group=False,
    demeaned=True,
    group_adjust=False,
)

mean_quant_rateret_bydate = mean_quant_ret_bydate.apply(
    utils.rate_of_return,
    axis=0,
    base_period=mean_quant_ret_bydate.columns[0],
)

compstd_quant_daily = std_quant_daily.apply(
    utils.std_conversion,
    axis=0,
    base_period=std_quant_daily.columns[0],
)
```

`by_date=True` retains one mean return per date and quintile. Because
`demeaned=True` and `group_adjust=False`, stock returns are adjusted by
subtracting the cleaned universe's mean return on each date. Within a
bucket, stocks contribute equally to its mean.

For each date, a bucket's standard error is its cross-sectional sample
standard deviation divided by the square root of its valid stock count:

```text
SE_quintile[q, t] = sample_std(stock_returns_in_quintile[q, t])
                    / sqrt(N_quintile[q, t])
```

This measures the cross-sectional standard error of that date's bucket
average, rather than the time-series standard deviation of bucket returns.
The rate and standard-error conversions put all horizons on the first
column's base period. Both conversions leave the values unchanged for this
single `1D` horizon.

[Back to TOC](#table-of-contents)

### 5.2 Calculate the top-minus-bottom spread

The tear sheet calls `performance.compute_mean_returns_spread()`. For these
five quintiles, the effective call is:

```python
spread, spread_se = performance.compute_mean_returns_spread(
    mean_quant_rateret_bydate,
    upper_quant=5,
    lower_quant=1,
    std_err=compstd_quant_daily,
)
```

| Argument | Effect |
| --- | --- |
| `mean_quant_rateret_bydate` | Supplies the date-level mean return for each quintile and horizon. |
| `upper_quant=5` | Selects the highest quintile as the long leg. The tear sheet selects the maximum quantile label present in the cleaned data. |
| `lower_quant=1` | Selects the lowest quintile as the short leg. The tear sheet selects the minimum quantile label present in the cleaned data. |
| `std_err` | Supplies the bucket standard errors used to approximate the spread's standard error. Does not change the spread returns themselves. |

The resulting date-level spread is:

```text
spread[t] = 0.5 * (R_quintile[5, t] - R_quintile[1, t])
```

The factor of 0.5 scales the portfolio to 100% gross exposure. Its stock
weights on each date are:

| Stock membership | Portfolio weight |
| --- | --- |
| Q5 | `+0.5 / N_quintile[5, t]` |
| Q1 | `-0.5 / N_quintile[1, t]` |
| Q2, Q3, or Q4 | `0` |

Although the bucket returns have been universe-demeaned, the same
universe-average return is subtracted from both legs and cancels in their
difference.

The spread standard error is approximated as:

```text
SE_spread[t] = 0.5 * sqrt(SE_quintile[5, t]**2 + SE_quintile[1, t]**2)
```

This formula omits covariance between the bucket returns. It does not apply
a time-series or Newey–West adjustment.

[Back to TOC](#table-of-contents)

### 5.3 Plot the spread, moving average, and error band

The chart is generated by:

```python
plotting.plot_mean_quantile_returns_spread_time_series(
    spread,
    std_err=spread_se,
    bandwidth=0.5,
    ax=ax_mean_quantile_returns_spread_ts,
)
```

| Argument | Effect |
| --- | --- |
| `spread` | Supplies the date-level spread returns as decimals. The plotting function multiplies them by 10,000 to display basis points. |
| `std_err=spread_se` | Supplies the standard errors used to draw the shaded band. |
| `bandwidth=0.5` | Sets the band to half a standard error on either side of each period's spread. Does not change the spread or its moving average. |
| `ax` | Supplies the axes for the chart. The tear sheet passes a list containing one axis per return horizon; this image has one `1D` horizon. |

The plotted elements are:

| Element | Calculation |
| --- | --- |
| Thin green line | Each date's spread, in basis points. |
| Orange line | Arithmetic moving average over 22 observations, labeled "1 month moving avg". |
| Blue shaded band | `spread[t] +/- 0.5 * SE_spread[t]`, converted to basis points. |
| Black horizontal line | Zero spread return. |

The moving average uses `.rolling(window=22).mean()`. For this daily
analysis, 22 observations approximate a trading month; the window counts
observations rather than calendar days. The shaded band is half a standard
error on either side, not a 95% confidence interval.

The vertical limits are set to plus and minus the 95th percentile of
absolute spread returns. Extreme observations or their error bands may
therefore extend beyond the visible chart. This changes the display limits,
not the underlying return series or its mean.

[Back to TOC](#table-of-contents)

### 5.4 Relationship to the table and the other return plots

The arithmetic average of the spread series is the approximately 1.171 bps
reported as "Mean Period Wise Spread (bps, 100% gross)" in section 1. It is
a return per `1D` holding period, before transaction costs, rather than an
annualized return.

The plot uses the same Q5 and Q1 period returns underlying the bars in
section 2 and the quintile curves in section 4. It subtracts their
date-level returns and halves the difference. It does not subtract their
already-compounded wealth curves.

This Q5-minus-Q1 portfolio is separate from section 3's median-split
aggregate portfolio, which also holds stocks outside the extreme quintiles.

[Back to TOC](#table-of-contents)

<!-- Plot reference definitions. Images are stored under docs/images/return_tear_sheet/. -->

[plot-mean-period-wise-return]: images/return_tear_sheet/plot-mean-period-wise-return.png
[plot-equal-weighted-cumulative-return]: images/return_tear_sheet/plot-equal-weighted-cumulative-return.png
[plot-cumulative-return-by-quantile]: images/return_tear_sheet/plot-cumulative-return-by-quantile.png
[plot-top-minus-bottom-spread]: images/return_tear_sheet/plot-top-minus-bottom-spread.png