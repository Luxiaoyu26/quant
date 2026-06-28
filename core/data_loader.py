from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import IO

import pandas as pd


CACHE_DIR = Path("data_cache")
OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
PROXY_ENV_KEYS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
]


def _disable_proxy_environment() -> None:
    for key in PROXY_ENV_KEYS:
        os.environ.pop(key, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"


def _date_to_akshare(value: str) -> str:
    return pd.to_datetime(value).strftime("%Y%m%d")


def _normalize_date(value: str) -> str:
    return pd.to_datetime(value).strftime("%Y-%m-%d")


def normalize_a_share_symbol(symbol: str) -> str:
    """Normalize A-share code to the 6-digit format required by AkShare.

    Accepts examples such as 600519, sh600519, 600519.SH, 000001.SZ.
    """
    symbol = symbol.strip().upper()
    match = re.search(r"(\d{6})", symbol)
    if not match:
        raise ValueError("A股代码需要包含 6 位数字，例如 600519、000001、300750。")
    return match.group(1)


def _normalize_source(source: str, market: str) -> str:
    normalized = (source or "").strip().lower()
    if market == "A股":
        aliases = {
            "": "auto",
            "auto": "auto",
            "自动": "auto",
            "eastmoney": "eastmoney",
            "东方财富": "eastmoney",
            "sina": "sina",
            "新浪": "sina",
            "local_csv": "local_csv",
            "本地csv": "local_csv",
            "本地 csv": "local_csv",
        }
        return aliases.get(normalized, normalized)
    return "yfinance" if normalized in {"", "auto", "yfinance"} else normalized


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("Price data is empty.")

    result = df.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [col[0] for col in result.columns]

    aliases = {
        "date": "Date",
        "日期": "Date",
        "open": "Open",
        "开盘": "Open",
        "high": "High",
        "最高": "High",
        "low": "Low",
        "最低": "Low",
        "close": "Close",
        "收盘": "Close",
        "volume": "Volume",
        "成交量": "Volume",
    }
    rename_map = {}
    for column in result.columns:
        key = str(column).strip()
        rename_map[column] = aliases.get(key, aliases.get(key.lower(), key))
    result = result.rename(columns=rename_map)

    if "Date" in result.columns:
        result["Date"] = pd.to_datetime(result["Date"], errors="coerce")
        result = result.set_index("Date")
    else:
        result.index = pd.to_datetime(result.index, errors="coerce")
        result.index.name = "Date"

    missing = [column for column in OHLCV_COLUMNS if column not in result.columns]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {missing}")

    result = result[OHLCV_COLUMNS].copy()
    for column in OHLCV_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result[~result.index.isna()]
    result = result.dropna(subset=OHLCV_COLUMNS)
    result = result[~result.index.duplicated(keep="last")].sort_index()
    result.index.name = "Date"
    if result.empty:
        raise ValueError("Price data is empty after normalization.")
    return result


def _safe_filename_part(value: str, fallback: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return safe or fallback


def _make_cache_key(
    market: str,
    symbol: str,
    start: str,
    end: str,
    adjust: str,
    source: str,
) -> str:
    normalized_market = (market or "A股").strip()
    normalized_symbol = (
        normalize_a_share_symbol(symbol)
        if normalized_market == "A股"
        else symbol.strip().upper()
    )
    normalized_start = _normalize_date(start)
    normalized_end = _normalize_date(end)
    normalized_adjust = (adjust or "none").strip().lower() or "none"
    normalized_source = _normalize_source(source, normalized_market)
    raw_key = "|".join(
        [
            normalized_market,
            normalized_symbol,
            normalized_start,
            normalized_end,
            normalized_adjust,
            normalized_source,
        ]
    )
    digest = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    market_part = "ashare" if normalized_market == "A股" else "global"
    parts = [
        market_part,
        _safe_filename_part(normalized_symbol, "symbol"),
        normalized_start.replace("-", ""),
        normalized_end.replace("-", ""),
        _safe_filename_part(normalized_adjust, "none"),
        _safe_filename_part(normalized_source, "source"),
        digest,
    ]
    return "_".join(parts) + ".csv"


def _read_cache(cache_path: str | Path) -> pd.DataFrame:
    return _normalize_ohlcv(pd.read_csv(Path(cache_path)))


def _write_cache(df: pd.DataFrame, cache_path: str | Path) -> None:
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_ohlcv(df)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    normalized.to_csv(temp_path, index=True, index_label="Date")
    temp_path.replace(path)


def clear_data_cache(cache_dir: str | Path = CACHE_DIR) -> int:
    directory = Path(cache_dir)
    if not directory.exists():
        return 0

    deleted_count = 0
    for cache_file in directory.rglob("*.csv"):
        if cache_file.is_file():
            cache_file.unlink()
            deleted_count += 1
    return deleted_count


def load_csv_data(file: str | Path | IO[bytes]) -> pd.DataFrame:
    """Load an uploaded/local CSV and normalize it to Date-indexed OHLCV."""
    return _normalize_ohlcv(pd.read_csv(file))


def _sina_symbol(code: str) -> str:
    if code.startswith(("4", "8")):
        return f"bj{code}"
    if code.startswith(("5", "6", "9")):
        return f"sh{code}"
    return f"sz{code}"


def load_a_share_data(
    symbol: str,
    start: str,
    end: str,
    adjust: str = "qfq",
    source: str = "auto",
    disable_proxy: bool = True,
) -> pd.DataFrame:
    """Load China A-share daily OHLCV data with AkShare.

    adjust options:
    - "": raw prices
    - "qfq": 前复权，适合多数技术分析/回测
    - "hfq": 后复权
    """
    try:
        import akshare as ak
    except ImportError as exc:
        raise ImportError("缺少 akshare，请先运行：pip install akshare") from exc

    if disable_proxy:
        _disable_proxy_environment()

    code = normalize_a_share_symbol(symbol)
    start_date = _date_to_akshare(start)
    end_date = _date_to_akshare(end)
    normalized_source = _normalize_source(source, "A股")

    def download(selected_source: str) -> pd.DataFrame:
        if selected_source == "eastmoney":
            data = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
        elif selected_source == "sina":
            data = ak.stock_zh_a_daily(
                symbol=_sina_symbol(code),
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
        else:
            raise ValueError(f"Unsupported A-share data source: {source}")
        return _normalize_ohlcv(data)

    if normalized_source != "auto":
        return download(normalized_source)

    errors = []
    for selected_source in ("eastmoney", "sina"):
        try:
            return download(selected_source)
        except Exception as exc:
            errors.append(f"{selected_source}: {exc}")
    raise RuntimeError("A股行情下载失败；" + "；".join(errors))


def load_us_stock_data(
    symbol: str,
    start: str,
    end: str,
    disable_proxy: bool = True,
) -> pd.DataFrame:
    """Download US/HK OHLCV data and normalize column names."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("缺少 yfinance，请先运行：pip install yfinance") from exc

    if disable_proxy:
        _disable_proxy_environment()

    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    df = yf.download(symbol, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"No data found for symbol: {symbol}")

    return _normalize_ohlcv(df)


def load_price_data(
    symbol: str,
    start: str,
    end: str,
    market: str = "A股",
    adjust: str = "qfq",
    source: str = "auto",
    disable_proxy: bool = True,
    use_cache: bool = True,
    cache_dir: str | Path = CACHE_DIR,
) -> pd.DataFrame:
    """Unified data loader.

    market: "A股" or "美股/港股"
    """
    normalized_market = (market or "A股").strip()
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty.")
    normalized_symbol = (
        normalize_a_share_symbol(symbol)
        if normalized_market == "A股"
        else symbol.strip().upper()
    )

    normalized_start = _normalize_date(start)
    normalized_end = _normalize_date(end)
    if normalized_start > normalized_end:
        raise ValueError("Start date must not be later than end date.")

    normalized_adjust = (adjust or "none").strip().lower() or "none"
    normalized_source = _normalize_source(source, normalized_market)
    cache_path = Path(cache_dir) / _make_cache_key(
        market=normalized_market,
        symbol=normalized_symbol,
        start=normalized_start,
        end=normalized_end,
        adjust=normalized_adjust,
        source=normalized_source,
    )

    if use_cache and cache_path.exists():
        try:
            return _read_cache(cache_path)
        except Exception:
            pass

    if normalized_market == "A股":
        df = load_a_share_data(
            symbol=normalized_symbol,
            start=normalized_start,
            end=normalized_end,
            adjust="" if normalized_adjust == "none" else normalized_adjust,
            source=normalized_source,
            disable_proxy=disable_proxy,
        )
    else:
        if normalized_source != "yfinance":
            raise ValueError(f"Unsupported US/HK data source: {source}")
        df = load_us_stock_data(
            symbol=normalized_symbol,
            start=normalized_start,
            end=normalized_end,
            disable_proxy=disable_proxy,
        )

    df = _normalize_ohlcv(df)
    if use_cache:
        try:
            _write_cache(df, cache_path)
        except OSError:
            pass
    return df
