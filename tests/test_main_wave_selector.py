from __future__ import annotations

import numpy as np
import pandas as pd

import selection.main_wave_selector as selector
from stock_pools.sector_map import STOCK_SECTOR_MAP


def make_prices(multiplier: float = 1.0) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=100, freq="D", name="Date")
    close = pd.Series(np.linspace(10, 20 * multiplier, len(index)), index=index)
    return pd.DataFrame(
        {
            "Open": close * 0.995,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": np.full(len(index), 10_000.0),
        },
        index=index,
    )


def test_selector_returns_ranked_candidates_and_skips_failed_symbol(monkeypatch):
    def fake_load(symbol, *args, **kwargs):
        if symbol == "601318":
            raise RuntimeError("download failed")
        multiplier = 1.1 if symbol == "600519" else 1.0
        return make_prices(multiplier)

    monkeypatch.setattr(selector, "load_price_data", fake_load)

    result = selector.run_main_wave_candidate_selection(
        ["600519", "000858", "601318"],
        start="2024-01-01",
        end="2024-04-09",
        top_n=2,
    )

    assert result["rank"].tolist() == [1, 2]
    assert result.iloc[0]["final_score"] >= result.iloc[1]["final_score"]
    assert set(result["symbol"]) == {"600519", "000858"}
    assert result["filter_pass"].all()
    assert any("601318" in error for error in result.attrs["errors"])
    assert {
        "sector",
        "ret_20",
        "ret_60",
        "volume_ratio_5_20",
        "volatility_20",
        "sector_strength_score",
        "main_wave_score",
        "raw_score",
        "near_high_score",
        "trend_structure_score",
        "volume_breakout_score",
        "risk_score",
        "near_high_20",
        "near_high_60",
        "sector_ret_5_mean",
        "sector_ret_20_mean",
        "sector_volume_strength",
        "sector_breakout_ratio",
    }.issubset(result.columns)
    assert (result["final_score"] <= result["main_wave_score"]).all()


def test_default_stock_pool_can_produce_candidates_without_network(monkeypatch):
    monkeypatch.setattr(selector, "load_price_data", lambda *args, **kwargs: make_prices())

    result = selector.run_main_wave_candidate_selection(
        list(STOCK_SECTOR_MAP),
        start="2024-01-01",
        end="2024-04-09",
        select_date="2024-04-05",
        top_n=20,
    )

    assert not result.empty
    assert len(result) == len(STOCK_SECTOR_MAP)
    assert (pd.to_datetime(result["feature_date"]) <= pd.Timestamp("2024-04-05")).all()


def test_selector_returns_standard_empty_result_when_all_downloads_fail(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(selector, "load_price_data", fail)
    result = selector.run_main_wave_candidate_selection(
        ["600519"], "2024-01-01", "2024-04-09"
    )

    assert result.empty
    assert {"rank", "symbol", "sector", "final_score"}.issubset(result.columns)
    assert result.attrs["errors"]
