import numpy as np
import pandas as pd

from . import utils


def hit_rate(
    factor_data: pd.DataFrame,
    returns_columns: list[str] | pd.Index | None = None,
    by_date: bool = False,
) -> pd.Series | pd.DataFrame:
    """Compute the directional hit rate of factor predictions.

    A prediction is counted as correct when the sign of ``factor`` matches the
    sign of a forward return column. Observations with missing values, zero
    factor values, or zero forward returns are excluded from the denominator.

    Args:
        factor_data: MultiIndex DataFrame containing a ``factor`` column and one
            or more forward return columns.
        returns_columns: Optional subset of forward return columns to evaluate.
            When omitted, all forward return columns detected by
            ``utils.get_forward_returns_columns`` are used.
        by_date: If ``True``, return hit rates for each date. Otherwise, return
            the overall hit rate for each forward return horizon.

    Returns:
        A Series indexed by forward return horizon when ``by_date`` is
        ``False``, otherwise a DataFrame indexed by date with one column per
        horizon.

    Raises:
        ValueError: If the input is missing a ``factor`` column or no forward
            return columns are available.
    """
    if "factor" not in factor_data.columns:
        raise ValueError("factor_data must contain a 'factor' column.")

    if returns_columns is None:
        returns_columns = utils.get_forward_returns_columns(factor_data.columns)
    else:
        returns_columns = pd.Index(returns_columns)

    if len(returns_columns) == 0:
        raise ValueError("factor_data must contain at least one forward return column.")

    forward_returns = factor_data.loc[:, returns_columns]
    factor_sign = np.sign(factor_data["factor"])
    return_sign = np.sign(forward_returns)

    valid = (
        return_sign.notna()
        & return_sign.ne(0)
        & factor_sign.notna().to_numpy()[:, None]
        & factor_sign.ne(0).to_numpy()[:, None]
    )
    correct = return_sign.eq(factor_sign, axis=0).where(valid)

    hit_rates = correct.astype(float)

    if by_date:
        date_index = factor_data.index.get_level_values("date")
        return hit_rates.groupby(date_index).mean()

    return hit_rates.mean()

