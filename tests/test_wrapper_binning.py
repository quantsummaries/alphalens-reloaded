"""Group metadata must not silently change the wrapper's factor buckets."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from alphalens import utils, wrapper


@pytest.fixture
def panel():
    index = pd.MultiIndex.from_product(
        [pd.bdate_range("2024-01-02", periods=3), range(20)],
        names=["date", "asset"],
    )
    return pd.DataFrame({
        "signal": np.tile(np.r_[np.arange(10), 100 + np.arange(10)], 3),
        "group": np.tile(np.repeat(["A", "B"], 10), 3),
        "1D": np.random.default_rng(42).normal(0, .01, len(index)),
    }, index=index)


def run_wrapper(data, tmp_path, **kwargs):
    # Keep real factor cleaning; isolate plotting and unrelated report generation.
    with (
        patch.object(wrapper, "information_analysis_wrapper", return_value={
            f"ic_{kind}": pd.DataFrame({"1D": [.1]}, index=[f"IC Mean ({kind})"])
            for kind in ["spearman", "pearson"]
        }),
        patch.object(wrapper, "return_analysis_wrapper", return_value={
            key: pd.DataFrame({"1D": [.01]})
            for key in ["mean_return_by_q", "std_err_by_q", "return_summary"]
        }) as returns,
        patch.object(wrapper, "turnover_analysis_wrapper", return_value={
            "turnover": pd.DataFrame({1: [.1]}),
            "factor_autocorr": pd.Series([.2]),
        }) as turnover,
    ):
        columns = ["1D"]
        wrapper.full_tear_sheet_wrapper(
            data, factors=["signal"], fwd_rtrn_cols=columns,
            output_dir=str(tmp_path), **kwargs,
        )
        assert columns == ["1D"]
        cleaned = returns.call_args.kwargs["data"]
        pd.testing.assert_frame_equal(cleaned, turnover.call_args.kwargs["data"])
        return cleaned


@pytest.mark.parametrize("mode", ["default", "pooled", "grouped"])
@pytest.mark.parametrize("use_bins", [False, True])
@pytest.mark.parametrize("group_flags", [False, True])
def test_bucketing_is_independent_of_group_reporting(
    panel, tmp_path, mode, use_bins, group_flags,
):
    buckets = {"quantiles": None, "bins": 5} if use_bins else {"quantiles": 5}
    grouped = mode == "grouped"
    options = {} if mode == "default" else {"binning_by_group": grouped}
    actual = run_wrapper(
        panel, tmp_path, group_neutral=group_flags, by_group=group_flags,
        **buckets, **options,
    )
    expected = utils.get_clean_factor(
        panel["signal"], panel[["1D"]], groupby=panel["group"],
        binning_by_group=grouped, **buckets,
    )
    pd.testing.assert_frame_equal(actual, expected)
    pooled = utils.get_clean_factor(
        panel["signal"], panel[["1D"]], groupby=panel["group"],
        binning_by_group=False, **buckets,
    )
    assert actual["factor_quantile"].equals(pooled["factor_quantile"]) != grouped


def test_default_preserves_constant_group_observations(panel, tmp_path):
    # Pooled quintiles are well-defined, but every individual group is constant.
    panel["signal"] = np.tile(np.repeat(np.arange(5), 4), 3)
    panel["group"] = np.tile(np.repeat(np.arange(5), 4), 3)
    actual = run_wrapper(panel, tmp_path)
    assert len(actual) == len(panel)
    assert actual["factor_quantile"].nunique() == 5


def test_default_without_group_column(panel, tmp_path):
    panel = panel.drop(columns="group")
    actual = run_wrapper(panel, tmp_path)
    expected = utils.get_clean_factor(panel["signal"], panel[["1D"]], quantiles=5)
    pd.testing.assert_frame_equal(actual, expected)


def test_group_binning_requires_group_column(panel, tmp_path):
    with patch.object(wrapper, "information_analysis_wrapper") as information:
        with pytest.raises(ValueError, match="requires a group column"):
            wrapper.full_tear_sheet_wrapper(
                panel.drop(columns="group"), factors=["signal"],
                fwd_rtrn_cols=["1D"], output_dir=str(tmp_path), binning_by_group=True,
            )
        information.assert_not_called()


def test_full_wrapper_preserves_each_factors_return_summary(panel, tmp_path):
    panel = panel.assign(second_signal=-panel["signal"])
    summaries = [
        pd.DataFrame({"1D": [0.01, 0.2], "5h50m": [0.03, 0.4]},
                     index=["Ann. alpha", "beta"]),
        pd.DataFrame({"1D": [-0.01, -0.2], "5h50m": [-0.03, -0.4]},
                     index=["Ann. alpha", "beta"]),
    ]
    panel["5h50m"] = panel["1D"] / 2
    original_summaries = [summary.copy(deep=True) for summary in summaries]
    with (
        patch.object(wrapper, "information_analysis_wrapper", side_effect=lambda **kwargs: {
            f"ic_{kind}": pd.DataFrame({"1D": [.1]}, index=[f"IC Mean ({kind})"])
            for kind in ["spearman", "pearson"]
        }),
        patch.object(wrapper, "return_analysis_wrapper", side_effect=[
            {
                "mean_return_by_q": pd.DataFrame({"1D": [.01]}),
                "std_err_by_q": pd.DataFrame({"1D": [.001]}),
                "return_summary": summary,
            }
            for summary in summaries
        ]),
        patch.object(wrapper, "turnover_analysis_wrapper", side_effect=lambda **kwargs: {
            "turnover": pd.DataFrame({1: [.1]}),
            "factor_autocorr": pd.Series([.2]),
        }),
    ):
        result = wrapper.full_tear_sheet_wrapper(
            panel, factors=["signal", "second_signal"],
            fwd_rtrn_cols=["1D", "5h50m"], output_dir=str(tmp_path),
        )
    summary = result["return_summary"]
    assert summary.columns.to_list() == ["factor", "1D", "5h50m"]
    assert summary["factor"].to_list() == ["signal", "signal", "second_signal", "second_signal"]
    for factor, expected, original in zip(
        ["signal", "second_signal"], original_summaries, summaries, strict=True,
    ):
        pd.testing.assert_frame_equal(
            summary.loc[summary["factor"] == factor].drop(columns="factor"), expected,
        )
        pd.testing.assert_frame_equal(original, expected)
