from __future__ import annotations

import numpy as np
import pandas as pd


def _numeric_column(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return pd.to_numeric(df[name], errors="coerce")


def _rank_with_fallback(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    if valid.empty:
        return pd.Series(0.0, index=numeric.index, dtype=float)
    return numeric.fillna(valid.median()).rank(pct=True).astype(float)


def _calculate_risk_score(volatility: pd.Series) -> pd.Series:
    score = pd.Series(0.0, index=volatility.index, dtype=float)
    score.loc[volatility <= 0.02] = 1.0
    score.loc[(volatility > 0.02) & (volatility <= 0.04)] = 0.8
    score.loc[(volatility > 0.04) & (volatility <= 0.06)] = 0.5
    score.loc[volatility > 0.06] = 0.2
    return score


def calculate_main_wave_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add resilient V2 main-wave precursor scores to a stock cross-section."""
    result = df.copy()
    close = _numeric_column(result, "Close")
    ma20 = _numeric_column(result, "ma20")
    ma60 = _numeric_column(result, "ma60")

    result["trend_structure_score"] = (
        close.gt(ma20).astype(float)
        + close.gt(ma60).astype(float)
        + ma20.gt(ma60).astype(float)
    ) / 3.0

    result["near_high_20_score"] = _rank_with_fallback(
        _numeric_column(result, "near_high_20")
    )
    result["near_high_60_score"] = _rank_with_fallback(
        _numeric_column(result, "near_high_60")
    )
    result["near_high_score"] = (
        0.5 * result["near_high_20_score"]
        + 0.5 * result["near_high_60_score"]
    )

    result["volume_ratio_5_20_score"] = _rank_with_fallback(
        _numeric_column(result, "volume_ratio_5_20")
    )
    result["volume_ratio_20_60_score"] = _rank_with_fallback(
        _numeric_column(result, "volume_ratio_20_60")
    )
    result["up_volume_ratio_20_score"] = _rank_with_fallback(
        _numeric_column(result, "up_volume_ratio_20")
    )
    result["volume_breakout_score"] = (
        0.40 * result["volume_ratio_5_20_score"]
        + 0.30 * result["volume_ratio_20_60_score"]
        + 0.30 * result["up_volume_ratio_20_score"]
    )

    result["ret_20_score"] = _rank_with_fallback(_numeric_column(result, "ret_20"))
    result["ret_60_score"] = _rank_with_fallback(_numeric_column(result, "ret_60"))
    result["risk_score"] = _calculate_risk_score(
        _numeric_column(result, "volatility_20")
    )
    result["risk_penalty_score"] = 0.05 * (1 - result["risk_score"])

    sector_score = _numeric_column(result, "sector_strength_score").fillna(0)
    result["main_wave_score"] = (
        0.20 * result["ret_20_score"]
        + 0.10 * result["ret_60_score"]
        + 0.15 * result["near_high_score"]
        + 0.15 * result["trend_structure_score"]
        + 0.15 * result["volume_breakout_score"]
        + 0.20 * sector_score
        + 0.05 * result["risk_score"]
    )
    result["raw_score"] = result["main_wave_score"]
    result["final_score"] = (
        result["raw_score"] - result["risk_penalty_score"]
    ).clip(lower=0)
    return result
