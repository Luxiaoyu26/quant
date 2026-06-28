from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def calculate_volume_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling volume, price direction and volatility features."""
    missing = [column for column in ("Close", "Volume") if column not in df.columns]
    if missing:
        raise ValueError(f"Volume-price features require columns: {missing}")

    result = df.copy()
    close = pd.to_numeric(result["Close"], errors="coerce")
    volume = pd.to_numeric(result["Volume"], errors="coerce")
    result["volume_ma5"] = volume.rolling(5).mean()
    result["volume_ma20"] = volume.rolling(20).mean()
    result["volume_ma60"] = volume.rolling(60).mean()
    result["volume_ratio_5_20"] = _safe_divide(
        result["volume_ma5"], result["volume_ma20"]
    )
    result["volume_ratio_20_60"] = _safe_divide(
        result["volume_ma20"], result["volume_ma60"]
    )
    result["pct_change"] = close.pct_change()
    result["up_day"] = result["pct_change"] > 0

    down_day = result["pct_change"] < 0
    up_count = result["up_day"].astype(int).rolling(20).sum()
    down_count = down_day.astype(int).rolling(20).sum()
    up_average = _safe_divide(
        volume.where(result["up_day"], 0).rolling(20).sum(), up_count
    )
    down_average = _safe_divide(
        volume.where(down_day, 0).rolling(20).sum(), down_count
    )
    result["up_volume_ratio_20"] = _safe_divide(up_average, down_average)
    result["volatility_20"] = result["pct_change"].rolling(20).std()
    return result
