from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def _to_series(values: Iterable[float] | pd.Series | None) -> pd.Series:
    if values is None:
        return pd.Series(dtype=float)
    if isinstance(values, pd.Series):
        series = values.copy()
    else:
        series = pd.Series(values, dtype=float)
    return pd.to_numeric(series, errors="coerce").dropna().astype(float)


def calculate_total_return(equity) -> float:
    values = _to_series(equity)
    if values.empty or values.iloc[0] == 0:
        return 0.0
    return float(values.iloc[-1] / values.iloc[0] - 1)


def calculate_max_drawdown(equity) -> float:
    values = _to_series(equity)
    if values.empty:
        return 0.0
    running_max = values.cummax().replace(0, np.nan)
    drawdown = (values / running_max - 1).replace([np.inf, -np.inf], np.nan).dropna()
    return float(drawdown.min()) if not drawdown.empty else 0.0


def calculate_annual_return(equity, periods_per_year: int = 252) -> float:
    values = _to_series(equity)
    periods = len(values) - 1
    if periods <= 0 or periods_per_year <= 0 or values.iloc[0] <= 0:
        return 0.0
    growth = values.iloc[-1] / values.iloc[0]
    if growth < 0:
        return 0.0
    return float(growth ** (periods_per_year / periods) - 1)


def calculate_sharpe_ratio(returns, periods_per_year: int = 252) -> float:
    values = _to_series(returns)
    if len(values) < 2 or periods_per_year <= 0:
        return 0.0
    volatility = values.std(ddof=1)
    if not np.isfinite(volatility) or volatility == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * values.mean() / volatility)
