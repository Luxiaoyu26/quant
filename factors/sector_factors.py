from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "symbol",
    "sector",
    "ret_5",
    "ret_20",
    "volume_ratio_5_20",
    "breakout_20",
]


def calculate_sector_strength(stock_feature_df: pd.DataFrame) -> pd.DataFrame:
    """Add sector-level statistics to a same-date stock cross-section."""
    missing = [column for column in REQUIRED_COLUMNS if column not in stock_feature_df.columns]
    if missing:
        raise ValueError(f"Sector strength missing required columns: {missing}")

    result = stock_feature_df.copy()
    group = result.groupby("sector", dropna=False)
    result["sector_ret_5_mean"] = group["ret_5"].transform("mean")
    result["sector_ret_20_mean"] = group["ret_20"].transform("mean")
    result["sector_volume_strength"] = group["volume_ratio_5_20"].transform("mean")
    breakout = result["breakout_20"].fillna(False).astype(float)
    result["sector_breakout_ratio"] = breakout.groupby(result["sector"], dropna=False).transform("mean")
    result["sector_stock_count"] = group["symbol"].transform("count")
    result["sector_strength_raw"] = (
        0.35 * result["sector_ret_5_mean"]
        + 0.35 * result["sector_ret_20_mean"]
        + 0.20 * result["sector_volume_strength"]
        + 0.10 * result["sector_breakout_ratio"]
    )
    result["sector_strength_score"] = result["sector_strength_raw"].rank(pct=True)
    return result
