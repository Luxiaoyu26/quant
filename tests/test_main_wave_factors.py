from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from factors.momentum_factors import calculate_momentum_features
from factors.risk_filters import apply_candidate_filters
from factors.sector_factors import calculate_sector_strength
from factors.volume_price_factors import calculate_volume_price_features
from stock_pools.sector_map import get_stock_sector


def make_prices(periods: int = 80) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=periods, freq="D", name="Date")
    close = pd.Series(np.arange(1, periods + 1, dtype=float), index=index)
    return pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": np.arange(1000, 1000 + periods, dtype=float),
        },
        index=index,
    )


@pytest.mark.parametrize(
    ("symbol", "sector"),
    [
        ("600519", "白酒"),
        ("600519.SH", "白酒"),
        ("sh600519", "白酒"),
        ("999999", "未知板块"),
    ],
)
def test_get_stock_sector_normalizes_common_symbol_formats(symbol, sector):
    assert get_stock_sector(symbol) == sector


def test_calculate_momentum_features_adds_expected_values():
    result = calculate_momentum_features(make_prices())

    assert result.iloc[-1]["ret_20"] == pytest.approx(80 / 60 - 1)
    assert result.iloc[-1]["ret_60"] == pytest.approx(80 / 20 - 1)
    assert result.iloc[-1]["near_high_20"] == pytest.approx(0)
    assert bool(result.iloc[-1]["breakout_20"]) is True
    assert result.iloc[-1]["relative_strength_20"] == pytest.approx(
        result.iloc[-1]["ret_20"]
    )


def test_calculate_momentum_features_handles_empty_and_missing_close():
    empty = calculate_momentum_features(pd.DataFrame(columns=["Close"]))
    assert empty.empty
    assert "ret_20" in empty.columns

    with pytest.raises(ValueError, match="Close"):
        calculate_momentum_features(pd.DataFrame({"Volume": [1]}))


def test_calculate_volume_price_features_adds_ratios_without_infinity():
    result = calculate_volume_price_features(make_prices())

    assert result.iloc[-1]["volume_ratio_5_20"] > 0
    assert result.iloc[-1]["volume_ratio_20_60"] > 0
    numeric = result[["volume_ratio_5_20", "volume_ratio_20_60", "up_volume_ratio_20"]]
    assert not np.isinf(numeric.to_numpy(dtype=float)).any()
    assert "volatility_20" in result.columns


def test_calculate_sector_strength_adds_group_statistics_and_score():
    frame = pd.DataFrame(
        {
            "symbol": ["600519", "000858", "600036"],
            "sector": ["白酒", "白酒", "银行"],
            "ret_5": [0.10, 0.06, 0.01],
            "ret_20": [0.20, 0.12, 0.02],
            "volume_ratio_5_20": [1.4, 1.2, 0.8],
            "breakout_20": [True, False, False],
        }
    )

    result = calculate_sector_strength(frame)

    liquor = result[result["sector"] == "白酒"]
    assert (liquor["sector_stock_count"] == 2).all()
    assert np.allclose(liquor["sector_ret_5_mean"], 0.08)
    assert result["sector_strength_score"].between(0, 1).all()


def test_apply_candidate_filters_keeps_rows_and_records_reasons():
    frame = pd.DataFrame(
        {
            "ret_20": [0.10, -0.20],
            "ret_60": [0.20, np.nan],
            "volatility_20": [0.02, 0.10],
            "Volume": [1000, 0],
            "volume_ratio_5_20": [1.0, 0.5],
            "Close": [12, 8],
            "ma20": [10, 10],
        }
    )

    result = apply_candidate_filters(frame)

    assert len(result) == 2
    assert bool(result.loc[0, "filter_pass"]) is True
    assert result.loc[0, "filter_reason"] == ""
    assert bool(result.loc[1, "filter_pass"]) is False
    assert "ret_60缺失" in result.loc[1, "filter_reason"]
    assert "成交量非正" in result.loc[1, "filter_reason"]
