from __future__ import annotations

import re


STOCK_SECTOR_MAP = {
    "600519": "白酒",
    "000858": "白酒",
    "600036": "银行",
    "000001": "银行",
    "601318": "保险",
    "300750": "新能源",
    "002594": "新能源",
    "600900": "电力",
    "000333": "家电",
    "601888": "旅游消费",
}


def _normalize_symbol(symbol: str) -> str:
    match = re.search(r"(\d{6})", str(symbol).strip().upper())
    return match.group(1) if match else ""


def get_stock_sector(symbol: str) -> str:
    """Return the mapped sector after normalizing common A-share formats."""
    return STOCK_SECTOR_MAP.get(_normalize_symbol(symbol), "未知板块")
