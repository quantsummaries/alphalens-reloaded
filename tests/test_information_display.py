"""Regression coverage for analysis table display and figure ownership."""

from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import pytest
from PIL import Image

from alphalens.wrapper import (
    full_tear_sheet_wrapper,
    information_analysis_wrapper,
    return_analysis_wrapper,
    turnover_analysis_wrapper,
)


@pytest.fixture
def information_data():
    index = pd.MultiIndex.from_product(
        [pd.date_range("2024-01-01", periods=20), list("ABCDEF")],
        names=["date", "asset"],
    )
    rng = np.random.default_rng(42)
    data = pd.DataFrame(
        {"factor": rng.normal(size=len(index)), "1D": rng.normal(size=len(index))},
        index=index,
    )
    data["factor_quantile"] = data.groupby(level="date")["factor"].rank().astype(int)
    return data


@pytest.mark.parametrize("tables_as_figures", [False, True])
def test_full_wrapper_forwards_table_display(
    information_data, tmp_path, tables_as_figures
):
    summary = pd.DataFrame({"1D": [0.1]})
    with (
        patch("alphalens.utils.get_clean_factor", return_value=information_data),
        patch(
            "alphalens.wrapper.information_analysis_wrapper",
            return_value={
                "ic_spearman": summary.copy(),
                "ic_pearson": summary.copy(),
            },
        ) as information,
        patch(
            "alphalens.wrapper.return_analysis_wrapper",
            return_value={
                "mean_return_by_q": summary.copy(),
                "std_err_by_q": summary.copy(),
            },
        ) as returns,
        patch(
            "alphalens.wrapper.turnover_analysis_wrapper",
            return_value={
                "turnover": summary.copy(),
                "factor_autocorr": summary.copy(),
            },
        ) as turnover,
    ):
        result = full_tear_sheet_wrapper(
            information_data.reset_index(),
            factors=["factor"],
            fwd_rtrn_cols=["1D"],
            output_dir=str(tmp_path),
            tables_as_figures=tables_as_figures,
        )
    for wrapper in [information, returns, turnover]:
        assert wrapper.call_count == 1
        assert wrapper.call_args.kwargs["tables_as_figures"] is tables_as_figures
    assert len(result) == 6


@pytest.mark.parametrize("tables_as_figures", [False, True])
def test_information_wrapper_returns_data_with_independent_display(
    information_data, tables_as_figures
):
    existing_figures = set(plt.get_fignums())
    try:
        with patch("alphalens.plotting.utils.print_table") as display:
            result = information_analysis_wrapper(
                information_data, tables_as_figures=tables_as_figures
            )
        assert display.call_count == (0 if tables_as_figures else 2)
        assert set(result) == {"ic_spearman", "ic_pearson"}
        for ic_type in ["spearman", "pearson"]:
            summary = result[f"ic_{ic_type}"]
            assert isinstance(summary, pd.DataFrame)
            assert list(summary.columns) == ["1D"]
            assert f"IC Mean ({ic_type})" in summary.index
        figures = set(plt.get_fignums()) - existing_figures
        assert len(figures) == (2 if tables_as_figures else 0)
        for number in figures:
            assert len(plt.figure(number).axes[0].tables) == 1
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)


@pytest.mark.parametrize("tables_as_figures", [False, True])
@pytest.mark.parametrize("analysis", ["returns", "turnover"])
def test_standalone_analysis_display(information_data, tables_as_figures, analysis):
    existing_figures = set(plt.get_fignums())
    wrapper = (
        return_analysis_wrapper if analysis == "returns" else turnover_analysis_wrapper
    )
    kwargs = (
        {"turnover_period": 1, "period_unit": "D"} if analysis == "turnover" else {}
    )
    try:
        with patch("alphalens.plotting.utils.print_table") as display:
            result = wrapper(
                information_data, tables_as_figures=tables_as_figures, **kwargs
            )
        assert display.call_count == (
            0 if tables_as_figures else (1 if analysis == "returns" else 2)
        )
        figures = set(plt.get_fignums()) - existing_figures
        assert len(figures) == int(tables_as_figures)
        assert all(
            isinstance(value, (pd.DataFrame, pd.Series)) for value in result.values()
        )
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)


@pytest.mark.parametrize("tables_as_figures", [False, True])
def test_grouped_information_returns_same_data_when_saved(
    information_data, tmp_path, tables_as_figures
):
    data = information_data.copy()
    data["group"] = np.tile([0, 0, 0, 1, 1, 1], 20)
    existing_figures = set(plt.get_fignums())
    try:
        with patch("alphalens.plotting.utils.print_table"):
            standalone = information_analysis_wrapper(
                data, by_group=True, tables_as_figures=tables_as_figures
            )
            with patch.object(PdfPages, "savefig"):
                saved = information_analysis_wrapper(
                    data,
                    by_group=True,
                    tables_as_figures=tables_as_figures,
                    tear_sheet_filepath=str(tmp_path / "grouped.pdf"),
                )
        for key in standalone:
            pd.testing.assert_frame_equal(standalone[key], saved[key])
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)


@pytest.mark.parametrize("extension", ["pdf", "png"])
@pytest.mark.parametrize("tables_as_figures", [False, True])
@pytest.mark.parametrize("analysis", ["information", "returns", "turnover"])
def test_analysis_export_owns_figures(
    information_data, tmp_path, extension, tables_as_figures, analysis
):
    existing_figures = set(plt.get_fignums())
    unrelated, ax = plt.subplots()
    ax.table(cellText=[["old table"]], loc="center")
    preserved_figures = set(plt.get_fignums())
    exported = []
    original_pdf_savefig = PdfPages.savefig
    original_savefig = Figure.savefig

    def capture_pdf(pdf, figure, **kwargs):
        exported.append(figure)
        return original_pdf_savefig(pdf, figure, **kwargs)

    def capture_png(figure, buffer, **kwargs):
        if extension == "pdf":
            return original_savefig(figure, buffer, **kwargs)
        exported.append(figure)
        # Keep this test focused on figure selection, without rasterizing large plots.
        Image.new("RGB", (2, 2)).save(buffer, format="PNG")

    try:
        with patch.object(PdfPages, "savefig", capture_pdf), patch.object(
            Figure, "savefig", capture_png
        ):
            # Repeated exports must not accumulate table figures.
            for attempt in range(2):
                exported.clear()
                destination = tmp_path / f"information-{attempt}.{extension}"
                wrapper = {
                    "information": information_analysis_wrapper,
                    "returns": return_analysis_wrapper,
                    "turnover": turnover_analysis_wrapper,
                }[analysis]
                kwargs = (
                    {"turnover_period": 1, "period_unit": "D"}
                    if analysis == "turnover"
                    else {}
                )
                with patch("alphalens.plotting.utils.print_table") as display:
                    result = wrapper(
                        information_data,
                        tables_as_figures=tables_as_figures,
                        tear_sheet_filepath=str(destination),
                        **kwargs,
                    )
                titles = [
                    axis.get_title()
                    for figure in exported
                    for axis in figure.axes
                    if axis.tables
                ]
                expected_titles = {
                    "information": [
                        "Information Analysis Summary (spearman)",
                        "Information Analysis Summary (pearson)",
                    ],
                    "returns": ["Returns Analysis"],
                    "turnover": ["Turnover Analysis"],
                }[analysis]
                assert titles == (expected_titles if tables_as_figures else [])
                assert display.call_count == (
                    0 if tables_as_figures else (1 if analysis == "returns" else 2)
                )
                assert len(exported) == (
                    3 if tables_as_figures and analysis == "information" else 1
                )
                assert unrelated not in exported
                assert set(plt.get_fignums()) == preserved_figures
                assert plt.figure(unrelated.number) is unrelated
                assert all(
                    isinstance(value, (pd.DataFrame, pd.Series))
                    for value in result.values()
                )
                assert destination.exists()
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)


@pytest.mark.parametrize("failure", ["plot", "save"])
def test_information_export_failure_preserves_caller_figures(
    information_data, tmp_path, failure
):
    existing_figures = set(plt.get_fignums())
    unrelated, _ = plt.subplots()
    preserved_figures = set(plt.get_fignums())
    target = (
        "alphalens.plotting.plot_ic_hist"
        if failure == "plot"
        else "alphalens.tears.PdfPages.savefig"
    )
    try:
        with patch(target, side_effect=RuntimeError("export failed")):
            with pytest.raises(RuntimeError, match="export failed"):
                information_analysis_wrapper(
                    information_data,
                    tear_sheet_filepath=str(tmp_path / "information.pdf"),
                )
        assert set(plt.get_fignums()) == preserved_figures
        assert plt.figure(unrelated.number) is unrelated
    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)
