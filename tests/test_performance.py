#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from unittest import TestCase

from numpy import nan
from pandas import (
    Series,
    DataFrame,
    date_range,
    MultiIndex,
    Index,
    DatetimeIndex,
    Categorical,
    CategoricalIndex,
)
from pandas.testing import assert_frame_equal, assert_series_equal
from pandas.tseries.offsets import BDay, Day, CDay
from parameterized import parameterized

from alphalens.performance import (
    compute_mean_returns_spread,
    factor_information_coefficient,
    mean_information_coefficient,
    mean_return_by_quantile,
    quantile_turnover,
    factor_rank_autocorrelation,
    factor_returns,
    factor_alpha_beta,
    cumulative_returns,
    factor_weights,
)
from alphalens.utils import (
    get_forward_returns_columns,
    get_clean_factor_and_forward_returns,
)


class PerformanceTestCase(TestCase):
    dr = date_range(start="2015-1-1", end="2015-1-2", name="date")
    tickers = ["A", "B", "C", "D"]
    factor = (
        DataFrame(index=dr, columns=tickers, data=[[1, 2, 3, 4], [4, 3, 2, 1]])
        .stack()
        .dropna()
        .rename("factor")
    )
    factor.index = factor.index.set_names(["date", "asset"])
    factor_data = DataFrame(
        {
            "factor": factor,
            "group": Series(
                index=factor.index,
                data=[1, 1, 2, 2, 1, 1, 2, 2],
                dtype="category",
            ),
        }
    )

    @parameterized.expand(
        [
            (
                factor_data,
                [4, 3, 2, 1, 1, 2, 3, 4],
                False,
                False,
                dr,
                [-1.0, -1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                False,
                False,
                dr,
                [1.0, 1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                False,
                True,
                MultiIndex.from_product(
                    [dr, Categorical([1, 2])], names=["date", "group"]
                ),
                [1.0, 1.0, 1.0, 1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                True,
                True,
                MultiIndex.from_product(
                    [dr, Categorical([1, 2])], names=["date", "group"]
                ),
                [1.0, 1.0, 1.0, 1.0],
            ),
        ]
    )
    def test_information_coefficient(
        self,
        factor_data,
        forward_returns,
        group_adjust,
        by_group,
        expected_ix,
        expected_ic_val,
    ):

        factor_data["1D"] = Series(index=factor_data.index, data=forward_returns)

        ic = factor_information_coefficient(
            factor_data=factor_data,
            group_adjust=group_adjust,
            by_group=by_group,
        )

        expected_ic_df = DataFrame(
            index=expected_ix,
            columns=["1D"],
            data=expected_ic_val,
        )

        assert_frame_equal(ic, expected_ic_df)

    @parameterized.expand(
        [
            (
                factor_data,
                [4, 3, 2, 1, 1, 2, 3, 4],
                False,
                False,
                "D",
                dr,
                [-1.0, -1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                False,
                False,
                "W",
                DatetimeIndex(["2015-01-04"], name="date", freq="W-SUN"),
                [1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                False,
                True,
                None,
                CategoricalIndex([1, 2], name="group"),
                [1.0, 1.0],
            ),
            (
                factor_data,
                [1, 2, 3, 4, 4, 3, 2, 1],
                False,
                True,
                "W",
                MultiIndex.from_product(
                    [
                        DatetimeIndex(["2015-01-04"], name="date", freq="W-SUN"),
                        Categorical([1, 2]),
                    ],
                    names=["date", "group"],
                ),
                [1.0, 1.0],
            ),
        ]
    )
    def test_mean_information_coefficient(
        self,
        factor_data,
        forward_returns,
        group_adjust,
        by_group,
        by_time,
        expected_ix,
        expected_ic_val,
    ):

        factor_data["1D"] = Series(index=factor_data.index, data=forward_returns)

        ic = mean_information_coefficient(
            factor_data,
            group_adjust=group_adjust,
            by_group=by_group,
            by_time=by_time,
        )

        expected_ic_df = DataFrame(
            index=expected_ix,
            columns=["1D"],
            data=expected_ic_val,
        )

        assert_frame_equal(ic, expected_ic_df)

    @parameterized.expand(
        [
            (
                [1.1, 1.2, 1.1, 1.2, 1.1, 1.2],
                [[1, 2, 1, 2, 1, 2], [1, 2, 1, 2, 1, 2], [1, 2, 1, 2, 1, 2]],
                2,
                False,
                [0.1, 0.2],
            ),
            (
                [1.1, 1.2, 1.1, 1.2, 1.1, 1.2],
                [[1, 2, 1, 2, 1, 2], [1, 2, 1, 2, 1, 2], [1, 2, 1, 2, 1, 2]],
                2,
                True,
                [0.1, 0.1, 0.2, 0.2],
            ),
            (
                [1.1, 1.1, 1.1, 1.2, 1.2, 1.2],
                [[1, 2, 3, 1, 2, 3], [1, 2, 3, 1, 2, 3], [1, 2, 3, 1, 2, 3]],
                3,
                False,
                [0.15, 0.15, 0.15],
            ),
            (
                [1.1, 1.1, 1.1, 1.2, 1.2, 1.2],
                [[1, 2, 3, 1, 2, 3], [1, 2, 3, 1, 2, 3], [1, 2, 3, 1, 2, 3]],
                3,
                True,
                [0.1, 0.2, 0.1, 0.2, 0.1, 0.2],
            ),
            (
                [1.5, 1.5, 1.2, 1.0, 1.0, 1.0],
                [[1, 1, 2, 2, 2, 2], [2, 2, 1, 2, 2, 2], [2, 2, 1, 2, 2, 2]],
                2,
                False,
                [0.3, 0.15],
            ),
            (
                [1.5, 1.5, 1.2, 1.0, 1.0, 1.0],
                [[1, 1, 3, 2, 2, 2], [3, 3, 1, 2, 2, 2], [3, 3, 1, 2, 2, 2]],
                3,
                False,
                [0.3, 0.0, 0.4],
            ),
            (
                [1.6, 1.6, 1.0, 1.0, 1.0, 1.0],
                [[1, 1, 2, 2, 2, 2], [2, 2, 1, 1, 1, 1], [2, 2, 1, 1, 1, 1]],
                2,
                False,
                [0.2, 0.4],
            ),
            (
                [1.6, 1.6, 1.0, 1.6, 1.6, 1.0],
                [[1, 1, 2, 1, 1, 2], [2, 2, 1, 2, 2, 1], [2, 2, 1, 2, 2, 1]],
                2,
                True,
                [0.2, 0.2, 0.4, 0.4],
            ),
        ]
    )
    def test_mean_return_by_quantile(
        self, daily_rets, factor, bins, by_group, expected_data
    ):
        """
        Test mean_return_by_quantile
        """
        tickers = ["A", "B", "C", "D", "E", "F"]

        factor_groups = {"A": 1, "B": 1, "C": 1, "D": 2, "E": 2, "F": 2}

        price_data = [
            [
                daily_rets[0] ** i,
                daily_rets[1] ** i,
                daily_rets[2] ** i,
                daily_rets[3] ** i,
                daily_rets[4] ** i,
                daily_rets[5] ** i,
            ]
            for i in range(1, 5)
        ]  # 4 days

        start = "2015-1-11"
        factor_end = "2015-1-13"
        price_end = "2015-1-14"  # 1D fwd returns

        price_index = date_range(start=start, end=price_end)
        price_index.name = "date"
        prices = DataFrame(index=price_index, columns=tickers, data=price_data)

        factor_index = date_range(start=start, end=factor_end)
        factor_index.name = "date"
        factor = DataFrame(index=factor_index, columns=tickers, data=factor).stack()

        factor_data = get_clean_factor_and_forward_returns(
            factor,
            prices,
            groupby=factor_groups,
            quantiles=None,
            bins=bins,
            periods=(1,),
        )

        mean_quant_ret, std_quantile = mean_return_by_quantile(
            factor_data,
            by_date=False,
            by_group=by_group,
            demeaned=False,
            group_adjust=False,
        )

        expected = DataFrame(
            index=mean_quant_ret.index.copy(),
            columns=mean_quant_ret.columns.copy(),
            data=expected_data,
        )
        expected.index.name = "factor_quantile"

        assert_frame_equal(mean_quant_ret, expected)

    @parameterized.expand(
        [
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                4.0,
                1,
                [nan, 1.0, 1.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                4.0,
                1,
                [nan, 1.0, 1.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                4.0,
                2,
                [nan, nan, 0.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                4.0,
                2,
                [nan, nan, 0.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                4.0,
                3,
                [nan, nan, nan, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                4.0,
                3,
                [nan, nan, nan, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                3.0,
                1,
                [nan, 0.0, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                3.0,
                1,
                [nan, 0.0, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                3.0,
                2,
                [nan, nan, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                3.0,
                2,
                [nan, nan, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                3.0,
                3,
                [nan, nan, nan, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                3.0,
                3,
                [nan, nan, nan, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                ],
                "1B",
                2.0,
                1,
                [nan, 1.0, 1.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                ],
                "1D",
                2.0,
                1,
                [nan, 1.0, 1.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                ],
                "1B",
                3.0,
                4,
                [nan, nan, nan, nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                ],
                "1D",
                3.0,
                4,
                [nan, nan, nan, nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                3.0,
                10,
                [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 3.0, 2.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                3.0,
                10,
                [nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, 0.0, 1.0],
            ),
        ]
    )
    def test_quantile_turnover(
        self, quantile_values, freq, test_quantile, period, expected_vals
    ):

        dr = date_range(
            start="2015-1-1",
            periods=len(quantile_values),
            freq=freq,
            name="date",
        )
        tickers = ["A", "B", "C", "D"]

        quantized_test_factor = (
            DataFrame(index=dr, columns=tickers, data=quantile_values)
            .rename_axis("asset", axis=1)
            .stack()
            .dropna()
        )

        to = quantile_turnover(quantized_test_factor, test_quantile, period)

        expected = Series(
            index=quantized_test_factor.index.levels[0], data=expected_vals
        ).rename(test_quantile)

        assert_series_equal(to, expected)

    @parameterized.expand(
        [
            (
                [[3, 4, 2, 1, nan], [3, 4, -2, -1, nan], [3, nan, nan, 1, 4]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                False,
                False,
                False,
                [
                    0.30,
                    0.40,
                    0.20,
                    0.10,
                    0.30,
                    0.40,
                    -0.20,
                    -0.10,
                    0.375,
                    0.125,
                    0.50,
                ],
            ),
            (
                [[3, 4, 2, 1, nan], [3, 4, -2, -1, nan], [3, nan, nan, 1, 4]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                True,
                False,
                False,
                [
                    0.125,
                    0.375,
                    -0.125,
                    -0.375,
                    0.20,
                    0.30,
                    -0.30,
                    -0.20,
                    0.10,
                    -0.50,
                    0.40,
                ],
            ),
            (
                [[3, 4, 2, 1, nan], [-3, 4, -2, 1, nan], [2, 2, 2, 3, 1]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                False,
                True,
                False,
                [
                    0.30,
                    0.40,
                    0.20,
                    0.10,
                    -0.30,
                    0.40,
                    -0.20,
                    0.10,
                    0.20,
                    0.20,
                    0.20,
                    0.30,
                    0.10,
                ],
            ),
            (
                [[3, 4, 2, 1, nan], [3, 4, -2, -1, nan], [3, nan, nan, 1, 4]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                True,
                True,
                False,
                [
                    0.25,
                    0.25,
                    -0.25,
                    -0.25,
                    0.25,
                    0.25,
                    -0.25,
                    -0.25,
                    -0.50,
                    0.0,
                    0.50,
                ],
            ),
            (
                [[3, 4, 2, 1, 5], [3, 4, -2, -1, 5], [3, nan, nan, 1, nan]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                False,
                False,
                True,
                [
                    0.20,
                    0.20,
                    0.20,
                    0.20,
                    0.20,
                    0.20,
                    0.20,
                    -0.20,
                    -0.20,
                    0.20,
                    0.50,
                    0.50,
                ],
            ),
            (
                [[1, 4, 2, 3, nan], [1, 4, -2, -3, nan], [3, nan, nan, 2, 7]],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                True,
                False,
                True,
                [
                    -0.25,
                    0.25,
                    -0.25,
                    0.25,
                    0.25,
                    0.25,
                    -0.25,
                    -0.25,
                    0.0,
                    -0.50,
                    0.50,
                ],
            ),
            (
                [
                    [3, 4, 2, 1, nan],
                    [-3, 4, -2, 1, nan],
                    [3, nan, nan, 1, 4],
                    [3, nan, nan, -1, 4],
                    [3, nan, nan, 1, -4],
                ],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                False,
                True,
                True,
                [
                    0.25,
                    0.25,
                    0.25,
                    0.25,
                    -0.25,
                    0.25,
                    -0.25,
                    0.25,
                    0.25,
                    0.50,
                    0.25,
                    0.25,
                    -0.50,
                    0.25,
                    0.25,
                    0.50,
                    -0.25,
                ],
            ),
            (
                [
                    [1, 4, 2, 3, nan],
                    [3, 4, -2, -1, nan],
                    [3, nan, nan, 2, 7],
                    [3, nan, nan, 2, -7],
                ],
                ["A", "B", "C", "D", "E"],
                {
                    "A": "Group1",
                    "B": "Group2",
                    "C": "Group1",
                    "D": "Group2",
                    "E": "Group1",
                },
                True,
                True,
                True,
                [
                    -0.25,
                    0.25,
                    0.25,
                    -0.25,
                    0.25,
                    0.25,
                    -0.25,
                    -0.25,
                    -0.50,
                    0.0,
                    0.50,
                    0.50,
                    0.0,
                    -0.50,
                ],
            ),
        ]
    )
    def test_factor_weights(
        self,
        factor_vals,
        tickers,
        groups,
        demeaned,
        group_adjust,
        equal_weight,
        expected_vals,
    ):

        index = date_range("1/12/2000", periods=len(factor_vals))
        factor = (
            DataFrame(index=index, columns=tickers, data=factor_vals).stack().dropna()
        )
        factor.index = factor.index.set_names(["date", "asset"])
        factor.name = "factor"

        factor_data = DataFrame()
        factor_data["factor"] = factor
        groups = Series(groups)
        factor_data["group"] = Series(
            index=factor.index,
            data=groups[factor.index.get_level_values("asset")].values,
        )

        weights = factor_weights(factor_data, demeaned, group_adjust, equal_weight)

        expected = Series(data=expected_vals, index=factor_data.index, name="factor")

        assert_series_equal(weights, expected)

    @parameterized.expand(
        [
            (
                [1, 2, 3, 4, 4, 3, 2, 1],
                [4, 3, 2, 1, 1, 2, 3, 4],
                False,
                [-1.25000, -1.25000],
            ),
            (
                [1, 1, 1, 1, 1, 1, 1, 1],
                [4, 3, 2, 1, 1, 2, 3, 4],
                False,
                [0.0, 0.0],
            ),
            (
                [1, 2, 3, 4, 4, 3, 2, 1],
                [4, 3, 2, 1, 1, 2, 3, 4],
                True,
                [-0.5, -0.5],
            ),
            (
                [1, 2, 3, 4, 1, 2, 3, 4],
                [1, 4, 1, 2, 1, 2, 2, 1],
                True,
                [1.0, 0.0],
            ),
            (
                [1, 1, 1, 1, 1, 1, 1, 1],
                [4, 3, 2, 1, 1, 2, 3, 4],
                True,
                [0.0, 0.0],
            ),
        ]
    )
    def test_factor_returns(
        self, factor_vals, fwd_return_vals, group_adjust, expected_vals
    ):

        factor_data = self.factor_data.copy()
        factor_data["1D"] = fwd_return_vals
        factor_data["factor"] = factor_vals

        factor_returns_s = factor_returns(
            factor_data=factor_data, demeaned=True, group_adjust=group_adjust
        )

        expected = DataFrame(
            index=self.dr,
            data=expected_vals,
            columns=get_forward_returns_columns(factor_data.columns),
        )

        assert_frame_equal(factor_returns_s, expected)

    @parameterized.expand([([1, 2, 3, 4, 1, 1, 1, 1], -1, 5.0 / 6.0)])
    def test_factor_alpha_beta(self, fwd_return_vals, alpha, beta):

        factor_data = self.factor_data.copy()
        factor_data["1D"] = fwd_return_vals

        ab = factor_alpha_beta(factor_data=factor_data)

        expected = DataFrame(
            columns=["1D"], index=["Ann. alpha", "beta"], data=[alpha, beta]
        )

        assert_frame_equal(ab.loc[["Ann. alpha", "beta"]], expected)
        self.assertEqual(ab.index.tolist(), ["Ann. alpha", "t-stat(alpha)", "beta", "t-stat(beta)"])

    @parameterized.expand(
        [
            (
                [1.0, 0.5, 1.0, 0.5, 0.5],
                "1D",
                "1D",
                [2.0, 3.0, 6.0, 9.0, 13.50],
            ),
            (
                [0.1, 0.1, 0.1, 0.1, 0.1],
                "1D",
                "1D",
                [1.1, 1.21, 1.331, 1.4641, 1.61051],
            ),
            (
                [-0.1, -0.1, -0.1, -0.1, -0.1],
                "1D",
                "1D",
                [0.9, 0.81, 0.729, 0.6561, 0.59049],
            ),
            (
                [1.0, 0.5, 1.0, 0.5, 0.5],
                "1B",
                "1D",
                [2.0, 3.0, 6.0, 9.0, 13.50],
            ),
            (
                [0.1, 0.1, 0.1, 0.1, 0.1],
                "1B",
                "1D",
                [1.1, 1.21, 1.331, 1.4641, 1.61051],
            ),
            (
                [-0.1, -0.1, -0.1, -0.1, -0.1],
                "1B",
                "1D",
                [0.9, 0.81, 0.729, 0.6561, 0.59049],
            ),
            (
                [1.0, 0.5, 1.0, 0.5, 0.5],
                "1CD",
                "1D",
                [2.0, 3.0, 6.0, 9.0, 13.50],
            ),
            (
                [0.1, 0.1, 0.1, 0.1, 0.1],
                "1CD",
                "1D",
                [1.1, 1.21, 1.331, 1.4641, 1.61051],
            ),
            (
                [-0.1, -0.1, -0.1, -0.1, -0.1],
                "1CD",
                "1D",
                [0.9, 0.81, 0.729, 0.6561, 0.59049],
            ),
        ]
    )
    def test_cumulative_returns(self, returns, ret_freq, period_len, expected_vals):
        if "CD" in ret_freq:
            ret_freq_class = CDay(weekmask="Tue Wed Thu Fri Sun")
            ret_freq = ret_freq_class
        elif "B" in ret_freq:
            ret_freq_class = BDay()
        else:
            ret_freq_class = Day()

        index = date_range("1/1/1999", periods=len(returns), freq=ret_freq)
        returns = Series(returns, index=index)

        cum_ret = cumulative_returns(returns)

        expected = Series(expected_vals, index=cum_ret.index)

        assert_series_equal(cum_ret, expected)

    @parameterized.expand(
        [
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                1,
                [nan, 1.0, 1.0, 1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                1,
                [nan, 1.0, 1.0, 1.0],
            ),
            (
                [
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1B",
                1,
                [nan, -1.0, -1.0, -1.0],
            ),
            (
                [
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                ],
                "1D",
                1,
                [nan, -1.0, -1.0, -1.0],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                ],
                "1B",
                3,
                [
                    nan,
                    nan,
                    nan,
                    1.0,
                    1.0,
                    1.0,
                    0.6,
                    -0.6,
                    -1.0,
                    1.0,
                    -0.6,
                    -1.0,
                ],
            ),
            (
                [
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                    [1.0, 2.0, 3.0, 4.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [2.0, 1.0, 4.0, 3.0],
                    [4.0, 3.0, 2.0, 1.0],
                ],
                "1D",
                3,
                [
                    nan,
                    nan,
                    nan,
                    1.0,
                    1.0,
                    1.0,
                    0.6,
                    -0.6,
                    -1.0,
                    1.0,
                    -0.6,
                    -1.0,
                ],
            ),
        ]
    )
    def test_factor_rank_autocorrelation(
        self, factor_values, freq, period, expected_vals
    ):

        dr = date_range(
            start="2015-1-1",
            periods=len(factor_values),
            freq=freq,
            name="date",
        )

        tickers = ["A", "B", "C", "D"]
        factor = (
            DataFrame(index=dr, columns=tickers, data=factor_values)
            .rename_axis("asset", axis=1)
            .stack()
            .dropna()
        )

        factor_df = DataFrame(data=factor, columns=["factor"])

        fa = factor_rank_autocorrelation(factor_df, period)
        expected = Series(index=dr, data=expected_vals)
        expected.name = period

        assert_series_equal(fa, expected)


    def test_single_asset_factor_weights_and_alpha_beta(self):
        dates = date_range("2020-01-01", periods=60, freq="B", name="date")
        idx = MultiIndex.from_product([dates, ["AAPL"]], names=["date", "asset"])
        factor = Series(1.0, index=idx, name="factor")
        prices = DataFrame(100.0, index=dates, columns=["AAPL"])

        factor_data = get_clean_factor_and_forward_returns(factor, prices, quantiles=1)
        weights = factor_weights(factor_data, demeaned=True)
        self.assertTrue((weights == 0.0).all())

        alpha_beta = factor_alpha_beta(factor_data, demeaned=True)
        self.assertTrue((alpha_beta.loc["Ann. alpha"] == 0.0).all())
        self.assertTrue((alpha_beta.loc["beta"] == 0.0).all())

        from alphalens.tears import create_summary_tear_sheet
        import matplotlib

        matplotlib.use("Agg")
        create_summary_tear_sheet(factor_data, long_short=True)


def test_mean_returns_spread_unit_gross_leverage():
    """A long/short spread is 50% long and 50% short, not 100% and 100%."""
    index = MultiIndex.from_product(
        [date_range("2020-01-02", periods=2, freq="D"), [1, 2]],
        names=["date", "factor_quantile"],
    )
    mean_returns = DataFrame({"1D": [0.01, 0.03, 0.02, 0.04]}, index=index)
    std_err = DataFrame({"1D": [0.002, 0.004, 0.002, 0.004]}, index=index)

    difference, joint_std = compute_mean_returns_spread(
        mean_returns, upper_quant=2, lower_quant=1, std_err=std_err
    )

    # Raw differences are 0.02. Half of that is one unit of gross leverage.
    assert_series_equal(
        difference["1D"],
        Series([0.01, 0.01], index=difference.index, name="1D"),
    )
    raw_std = (0.002**2 + 0.004**2) ** 0.5
    assert_series_equal(
        joint_std["1D"],
        Series([raw_std / 2, raw_std / 2], index=joint_std.index, name="1D"),
    )

    difference_only, no_err = compute_mean_returns_spread(mean_returns, 2, 1)
    assert no_err is None
    assert_series_equal(difference_only["1D"], difference["1D"])
