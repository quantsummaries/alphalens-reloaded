from unittest import TestCase

import pandas as pd

from alphalens.extra import hit_rate


class ExtraTestCase(TestCase):
    def setUp(self):
        index = pd.MultiIndex.from_tuples(
            [
                (pd.Timestamp("2024-01-01"), "A"),
                (pd.Timestamp("2024-01-01"), "B"),
                (pd.Timestamp("2024-01-01"), "C"),
                (pd.Timestamp("2024-01-02"), "A"),
                (pd.Timestamp("2024-01-02"), "B"),
                (pd.Timestamp("2024-01-02"), "C"),
            ],
            names=["date", "asset"],
        )
        self.factor_data = pd.DataFrame(
            {
                "factor": [1.0, -1.0, 0.0, 1.0, -1.0, 1.0],
                "1D": [0.10, -0.20, 0.50, -0.10, -0.20, 0.00],
                "5D": [0.10, 0.20, -0.30, float("nan"), -0.10, 0.10],
            },
            index=index,
        )

    def test_hit_rate_computes_overall_rate_per_horizon(self):
        result = hit_rate(self.factor_data)
        self.assertIsInstance(result, pd.Series)

        expected = pd.Series({"1D": 0.75, "5D": 0.75})

        pd.testing.assert_series_equal(result, expected)

    def test_hit_rate_can_be_grouped_by_date(self):
        result = hit_rate(self.factor_data, by_date=True)
        self.assertIsInstance(result, pd.DataFrame)

        expected = pd.DataFrame(
            {
                "1D": [1.0, 0.5],
                "5D": [0.5, 1.0],
            },
            index=pd.Index(
                [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")],
                name="date",
            ),
        )

        pd.testing.assert_frame_equal(result, expected)

    def test_hit_rate_requires_factor_and_forward_returns(self):
        with self.assertRaisesRegex(ValueError, "factor"):
            hit_rate(self.factor_data.drop(columns=["factor"]))

        with self.assertRaisesRegex(ValueError, "forward return"):
            hit_rate(self.factor_data[["factor"]])


