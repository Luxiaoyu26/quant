from __future__ import annotations

import pandas as pd

from core.backtester import run_backtest


def test_run_backtest_does_not_join_duplicate_target_position():
    index = pd.date_range("2024-01-02", periods=3, freq="D", name="Date")
    prices = pd.DataFrame(
        {
            "Open": [10.0, 10.2, 10.4],
            "High": [10.5, 10.7, 10.9],
            "Low": [9.8, 10.0, 10.2],
            "Close": [10.2, 10.4, 10.6],
            "Volume": [1000, 1100, 1200],
            "Position": [0, 1, 1],
        },
        index=index,
    )

    result, trades, metrics = run_backtest(
        prices,
        lot_size=1,
        min_commission=0,
        enable_t1=False,
        enable_limit_filter=False,
    )

    assert result.columns.tolist().count("Target_Position") == 1
    assert result["Target_Position"].tolist() == [0, 1, 1]
    assert "Equity" in result.columns
    assert isinstance(metrics, dict)
