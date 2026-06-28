from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from factors.main_wave_scores import calculate_main_wave_scores


def score_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Close": [12.0, 9.0, 10.0, 11.0, 8.0],
            "ma20": [10.0, np.nan, 11.0, 10.5, 9.0],
            "ma60": [8.0, 8.0, np.nan, 10.0, 10.0],
            "near_high_20": [-0.01, -0.10, np.nan, -0.03, -0.20],
            "near_high_60": [0.0, -0.15, -0.08, np.nan, -0.25],
            "volume_ratio_5_20": [2.0, 1.0, np.nan, 1.4, 0.7],
            "volume_ratio_20_60": [1.5, np.nan, 0.8, 1.1, 0.6],
            "up_volume_ratio_20": [np.nan, np.nan, np.nan, np.nan, np.nan],
            "ret_20": [0.30, 0.10, 0.05, 0.20, -0.05],
            "ret_60": [0.50, 0.15, 0.08, 0.30, -0.10],
            "volatility_20": [0.02, 0.04, 0.06, 0.07, np.nan],
            "sector_strength_score": [1.0, 0.6, 0.4, 0.8, 0.2],
        }
    )


def test_v2_scores_add_all_fields_and_expected_trend_structure():
    result = calculate_main_wave_scores(score_frame())

    expected_columns = {
        "trend_structure_score",
        "near_high_score",
        "volume_breakout_score",
        "risk_score",
        "risk_penalty_score",
        "main_wave_score",
        "raw_score",
        "final_score",
    }
    assert expected_columns.issubset(result.columns)
    assert result.loc[0, "trend_structure_score"] == pytest.approx(1.0)
    assert result.loc[1, "trend_structure_score"] == pytest.approx(1 / 3)
    assert result.loc[2, "trend_structure_score"] == pytest.approx(0.0)


def test_near_high_and_volume_breakout_scores_are_resilient_to_missing_values():
    result = calculate_main_wave_scores(score_frame())

    assert result.loc[0, "near_high_score"] > result.loc[4, "near_high_score"]
    assert result.loc[0, "volume_breakout_score"] > result.loc[4, "volume_breakout_score"]
    assert result["near_high_score"].notna().all()
    assert result["volume_breakout_score"].notna().all()
    assert result["up_volume_ratio_20_score"].eq(0).all()


def test_risk_score_uses_requested_bands_and_penalty():
    result = calculate_main_wave_scores(score_frame())

    assert result["risk_score"].tolist() == pytest.approx([1.0, 0.8, 0.5, 0.2, 0.0])
    assert result["risk_penalty_score"].tolist() == pytest.approx(
        [0.0, 0.01, 0.025, 0.04, 0.05]
    )


def test_main_wave_and_final_score_follow_v2_formula():
    result = calculate_main_wave_scores(score_frame())
    row = result.iloc[0]
    expected = (
        0.20 * row["ret_20_score"]
        + 0.10 * row["ret_60_score"]
        + 0.15 * row["near_high_score"]
        + 0.15 * row["trend_structure_score"]
        + 0.15 * row["volume_breakout_score"]
        + 0.20 * row["sector_strength_score"]
        + 0.05 * row["risk_score"]
    )

    assert row["main_wave_score"] == pytest.approx(expected)
    assert row["raw_score"] == pytest.approx(row["main_wave_score"])
    assert row["final_score"] == pytest.approx(
        max(row["raw_score"] - row["risk_penalty_score"], 0)
    )
    assert result["final_score"].ge(0).all()
