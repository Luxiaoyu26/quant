from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def check_ohlcv_data(df: pd.DataFrame) -> dict[str, object]:
    """Inspect OHLCV data without mutating it and return machine-readable issues."""
    issues: list[str] = []

    if df is None or df.empty:
        issues.append("dataframe_empty")

    columns = set() if df is None else set(df.columns)
    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in columns]
    if missing:
        issues.append(f"missing_columns: {', '.join(missing)}")

    if df is None or not isinstance(df.index, pd.DatetimeIndex):
        issues.append("index_not_datetime")
    elif df.index.duplicated().any():
        issues.append("duplicate_dates")

    if df is not None and not df.empty:
        available = [column for column in REQUIRED_OHLCV_COLUMNS if column in df.columns]
        if available and df[available].isna().any().any():
            issues.append("missing_values")

        price_columns = [column for column in ["Open", "High", "Low", "Close"] if column in df.columns]
        if price_columns and (df[price_columns] <= 0).any().any():
            issues.append("non_positive_prices")
        if {"High", "Low"}.issubset(df.columns) and (df["High"] < df["Low"]).any():
            issues.append("high_below_low")
        if "Volume" in df.columns and (df["Volume"] < 0).any():
            issues.append("negative_volume")

    return {"ok": not issues, "issues": issues}
