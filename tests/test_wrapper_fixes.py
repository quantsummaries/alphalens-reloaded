import importlib
import warnings

import pandas as pd
import pytest

import alphalens.wrapper as wrapper


def test_return_wrapper_honors_by_group_without_save(monkeypatch):
    dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
    assets = ["A", "B", "C", "D"]
    index = pd.MultiIndex.from_product([dates, assets], names=["date", "asset"])
    data = pd.DataFrame(
        {
            "factor": [1.0, 2.0, 3.0, 4.0, 1.5, 2.5, 3.5, 4.5],
            "factor_quantile": [1, 1, 2, 2, 1, 1, 2, 2],
            "group": ["g1", "g1", "g2", "g2", "g1", "g1", "g2", "g2"],
            "1D": [0.01, 0.02, 0.03, 0.04, -0.01, 0.00, 0.01, 0.02],
        },
        index=index,
    )

    calls = []

    def fake_mean_return_by_quantile(
        factor_data, by_date=False, by_group=False, demeaned=True, group_adjust=False
    ):
        calls.append({"by_date": by_date, "by_group": by_group})
        if by_date and by_group:
            idx = pd.MultiIndex.from_product(
                [[1, 2], dates, ["g1", "g2"]],
                names=["factor_quantile", "date", "group"],
            )
        elif by_date:
            idx = pd.MultiIndex.from_product(
                [[1, 2], dates], names=["factor_quantile", "date"]
            )
        elif by_group:
            idx = pd.MultiIndex.from_product(
                [[1, 2], ["g1", "g2"]], names=["factor_quantile", "group"]
            )
        else:
            idx = pd.Index([1, 2], name="factor_quantile")
        frame = pd.DataFrame({"1D": [0.01] * len(idx)}, index=idx)
        return frame, frame

    monkeypatch.setattr(
        wrapper.alphalens.performance,
        "mean_return_by_quantile",
        fake_mean_return_by_quantile,
    )
    monkeypatch.setattr(
        wrapper.alphalens.performance,
        "factor_returns",
        lambda *args, **kwargs: pd.DataFrame({"1D": [0.001, 0.002]}, index=dates),
    )
    monkeypatch.setattr(
        wrapper.alphalens.performance,
        "factor_alpha_beta",
        lambda *args, **kwargs: pd.DataFrame({"1D": [0.01, 0.2]}, index=["Ann. alpha", "beta"]),
    )
    monkeypatch.setattr(
        wrapper.alphalens.performance,
        "compute_mean_returns_spread",
        lambda *args, **kwargs: (pd.Series({"1D": 0.001}), None),
    )
    monkeypatch.setattr(
        wrapper.alphalens.plotting,
        "plot_returns_table",
        lambda *args, **kwargs: pd.DataFrame({"1D": [0.0]}, index=["ok"]),
    )

    wrapper.return_analysis_wrapper(
        data=data,
        by_group=True,
        tear_sheet_filepath=None,
        tables_as_figures=False,
    )

    assert len(calls) == 3
    assert calls[0] == {"by_date": False, "by_group": True}
    # The returned breakout uses groups; the displayed overall table pools
    # assets directly, matching the saved tear sheet's aggregation.
    assert calls[1] == {"by_date": False, "by_group": False}
    assert calls[2] == {"by_date": True, "by_group": False}


def test_full_wrapper_rejects_empty_factors(tmp_path):
    index = pd.MultiIndex.from_product(
        [pd.to_datetime(["2024-01-01"]), ["A"]], names=["date", "asset"]
    )
    data = pd.DataFrame({"1D": [0.01], "signal": [1.0]}, index=index)

    with pytest.raises(ValueError, match="at least one factor"):
        wrapper.full_tear_sheet_wrapper(
            data=data,
            factors=[],
            fwd_rtrn_cols=["1D"],
            output_dir=str(tmp_path),
        )


def test_full_wrapper_rejects_missing_factor_columns(tmp_path):
    index = pd.MultiIndex.from_product(
        [pd.to_datetime(["2024-01-01"]), ["A"]], names=["date", "asset"]
    )
    data = pd.DataFrame({"1D": [0.01], "signal": [1.0]}, index=index)

    with pytest.raises(ValueError, match="Factor columns not found"):
        wrapper.full_tear_sheet_wrapper(
            data=data,
            factors=["missing_signal"],
            fwd_rtrn_cols=["1D"],
            output_dir=str(tmp_path),
        )


def test_wrapper_reload_does_not_add_global_warning_filter():
    message = "'freq' not set in factor_data index: assuming business day"

    def count_filters():
        return sum(
            1
            for filt in warnings.filters
            if len(filt) > 1 and getattr(filt[1], "pattern", None) == message
        )

    before = count_filters()
    importlib.reload(wrapper)
    after = count_filters()
    assert after == before
