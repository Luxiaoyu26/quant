from __future__ import annotations

import pandas as pd

from core.data_quality import check_ohlcv_data


def test_check_ohlcv_data_accepts_valid_prices():
    df = pd.DataFrame(
        {
            "Open": [10.0, 10.2],
            "High": [10.5, 10.7],
            "Low": [9.8, 10.0],
            "Close": [10.2, 10.4],
            "Volume": [1000, 1200],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
    )

    assert check_ohlcv_data(df) == {"ok": True, "issues": []}


def test_check_ohlcv_data_reports_all_detectable_issues():
    duplicate_index = pd.to_datetime(["2024-01-02", "2024-01-02"])
    df = pd.DataFrame(
        {
            "Open": [0.0, None],
            "High": [8.0, 12.0],
            "Low": [9.0, 10.0],
            "Close": [10.0, 11.0],
            "Volume": [-1, 100],
        },
        index=duplicate_index,
    )

    result = check_ohlcv_data(df)

    assert result["ok"] is False
    assert set(result["issues"]) == {
        "duplicate_dates",
        "missing_values",
        "non_positive_prices",
        "high_below_low",
        "negative_volume",
    }


def test_check_ohlcv_data_handles_empty_missing_columns_and_bad_index():
    empty_result = check_ohlcv_data(pd.DataFrame())
    bad_shape_result = check_ohlcv_data(pd.DataFrame({"Open": [1]}))

    assert "dataframe_empty" in empty_result["issues"]
    assert any(issue.startswith("missing_columns:") for issue in empty_result["issues"])
    assert "index_not_datetime" in bad_shape_result["issues"]
    assert any(issue.startswith("missing_columns:") for issue in bad_shape_result["issues"])
