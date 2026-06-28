from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandas.testing as pdt
import pytest

import core.data_loader as data_loader


def sample_prices() -> pd.DataFrame:
    index = pd.to_datetime(["2024-01-02", "2024-01-03"])
    index.name = "Date"
    return pd.DataFrame(
        {
            "Open": [10.0, 10.5],
            "High": [11.0, 11.5],
            "Low": [9.5, 10.0],
            "Close": [10.8, 11.2],
            "Volume": [1000, 1200],
            "Ignored": [1, 2],
        },
        index=index,
    )


def test_load_price_data_writes_then_reads_cache(tmp_path, monkeypatch):
    calls = []

    def fake_loader(symbol, start, end, adjust="qfq", source="auto", disable_proxy=True):
        calls.append((symbol, start, end, adjust, source, disable_proxy))
        return sample_prices()

    monkeypatch.setattr(data_loader, "load_a_share_data", fake_loader)

    first = data_loader.load_price_data(
        " 600519.SH ",
        "2024/01/02",
        "2024-01-03",
        market="A股",
        adjust="qfq",
        source="东方财富",
        disable_proxy=True,
        cache_dir=tmp_path,
    )
    second = data_loader.load_price_data(
        "600519",
        "2024-01-02",
        "2024-01-03",
        market="A股",
        adjust="qfq",
        source="东方财富",
        disable_proxy=True,
        cache_dir=tmp_path,
    )

    assert len(calls) == 1
    assert len(list(tmp_path.glob("*.csv"))) == 1
    assert list(second.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert second.index.name == "Date"
    assert isinstance(second.index, pd.DatetimeIndex)
    pdt.assert_frame_equal(first, second, check_freq=False)


def test_load_price_data_can_disable_cache(tmp_path, monkeypatch):
    calls = 0

    def fake_loader(*args, **kwargs):
        nonlocal calls
        calls += 1
        return sample_prices()

    monkeypatch.setattr(data_loader, "load_us_stock_data", fake_loader)

    for _ in range(2):
        data_loader.load_price_data(
            "aapl",
            "2024-01-02",
            "2024-01-03",
            market="美股/港股",
            adjust="none",
            source="yfinance",
            use_cache=False,
            cache_dir=tmp_path,
        )

    assert calls == 2
    assert list(tmp_path.glob("*.csv")) == []


def test_corrupt_cache_falls_back_to_network_and_replaces_it(tmp_path, monkeypatch):
    cache_name = data_loader._make_cache_key(
        market="美股/港股",
        symbol="AAPL",
        start="2024-01-02",
        end="2024-01-03",
        adjust="none",
        source="yfinance",
    )
    cache_path = tmp_path / cache_name
    tmp_path.mkdir(parents=True, exist_ok=True)
    cache_path.write_text("not,a,valid,price,cache\n1,2,3,4,5\n", encoding="utf-8")
    calls = 0

    def fake_loader(*args, **kwargs):
        nonlocal calls
        calls += 1
        return sample_prices()

    monkeypatch.setattr(data_loader, "load_us_stock_data", fake_loader)

    result = data_loader.load_price_data(
        "AAPL",
        "2024-01-02",
        "2024-01-03",
        market="美股/港股",
        adjust="none",
        source="yfinance",
        cache_dir=tmp_path,
    )

    assert calls == 1
    assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
    reread = data_loader._read_cache(cache_path)
    pdt.assert_frame_equal(result, reread, check_freq=False)


def test_clear_data_cache_only_deletes_csv_files(tmp_path):
    (tmp_path / "nested").mkdir(parents=True)
    (tmp_path / "one.csv").write_text("x", encoding="utf-8")
    (tmp_path / "nested" / "two.csv").write_text("x", encoding="utf-8")
    keep = tmp_path / "keep.txt"
    keep.write_text("keep", encoding="utf-8")

    deleted = data_loader.clear_data_cache(tmp_path)

    assert deleted == 2
    assert keep.exists()
    assert not list(tmp_path.rglob("*.csv"))


def test_clear_data_cache_handles_missing_directory(tmp_path):
    missing = tmp_path / "missing"
    assert data_loader.clear_data_cache(missing) == 0


def test_load_csv_data_normalizes_date_and_ohlcv(tmp_path):
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume,extra\n"
        "2024-01-02,10,11,9,10.5,1000,x\n",
        encoding="utf-8",
    )

    result = data_loader.load_csv_data(csv_path)

    assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert result.index.name == "Date"
    assert result.index[0] == pd.Timestamp("2024-01-02")


def test_load_price_data_rejects_empty_symbol(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        data_loader.load_price_data(
            " ",
            "2024-01-02",
            "2024-01-03",
            cache_dir=tmp_path,
        )
