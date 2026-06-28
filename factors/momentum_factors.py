from __future__ import annotations

import pandas as pd


MOMENTUM_COLUMNS = [
    "ret_5",
    "ret_10",
    "ret_20",
    "ret_60",
    "ma20",
    "ma60",
    "high_20",
    "high_60",
    "near_high_20",
    "near_high_60",
    "breakout_20",
    "breakout_60",
    "relative_strength_20",
]


def calculate_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add momentum and breakout features without downloading data."""
    if "Close" not in df.columns:
        raise ValueError("Momentum features require a Close column.")

    result = df.copy()
    close = pd.to_numeric(result["Close"], errors="coerce")
    for window in (5, 10, 20, 60):
        result[f"ret_{window}"] = close / close.shift(window) - 1

    result["ma20"] = close.rolling(20).mean()
    result["ma60"] = close.rolling(60).mean()
    result["high_20"] = close.rolling(20).max()
    result["high_60"] = close.rolling(60).max()
    result["near_high_20"] = close / result["high_20"] - 1
    result["near_high_60"] = close / result["high_60"] - 1
    result["breakout_20"] = close >= result["high_20"].shift(1)
    result["breakout_60"] = close >= result["high_60"].shift(1)
    result["relative_strength_20"] = result["ret_20"]
    return result
